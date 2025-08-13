# auth.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
)
from flask_login import login_user, logout_user, current_user, login_required
from models import User, Level, Stream
from otp_service import generate_otp, send_otp_email, verify_otp
from extensions import db, oauth

auth_bp = Blueprint('auth', __name__)

# --- OAuth Configuration (unchanged) ---
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)
oauth.register(
    name='facebook',
    api_base_url='https://graph.facebook.com/v19.0/',
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    client_kwargs={'scope': 'email public_profile'},
    userinfo_endpoint='me?fields=id,name,email,picture'
)

# --- NEW: API Route to check email status ---
@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    """Checks if an email exists and returns its provider type."""
    email = request.json.get('email')
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required.'}), 400

    user = User.query.filter_by(email=email).first()

    if user:
        # User exists, return their provider
        print(f"Login attempt for {email}. Status: User exists. Provider: {user.provider}.")
        return jsonify({'status': 'exists', 'provider': user.provider})
    else:
        # User does not exist, they can register
        print(f"Login attempt for {email}. Status: New user.")
        return jsonify({'status': 'new_user'})

# --- MODIFIED: Unified Login/Registration Page ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles both login and registration flows."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        # This part handles the final password submission for email-based login
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.provider != 'email':
            flash(f'This account was created using {user.provider.capitalize()}. Please use that method to log in.', 'warning')
            return redirect(url_for('auth.login'))

        if user and user.check_password(password):
            login_user(user)
            if not user.streams:
                return redirect(url_for('profile.setup'))
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))
            
    # For GET requests, render the new unified template
    return render_template('login.html')

# The old /register route is no longer needed, but we keep it to avoid breaking old links
@auth_bp.route('/register')
def register():
    return redirect(url_for('auth.login'))

# --- API Routes for Registration ---

@auth_bp.route('/get_streams/<int:level_id>')
@login_required
def get_streams(level_id):
    streams = Stream.query.filter_by(level_id=level_id).order_by(Stream.name).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in streams])

@auth_bp.route('/start_registration', methods=['POST'])
def start_registration():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'success': False, 'message': 'Email is required.'}), 400

    # We assume the frontend has already checked that this is a new user
    session['auth_flow_email'] = email
    
    try:
        otp = generate_otp(email)
        if send_otp_email(email, otp):
            return jsonify({'success': True, 'message': 'An OTP has been sent to your email.'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP email.'}), 500
    except Exception as e:
        current_app.logger.error(f"OTP sending failed: {e}")
        return jsonify({'success': False, 'message': 'An internal error occurred while sending OTP.'}), 500

@auth_bp.route('/verify_otp', methods=['POST'])
def verify_otp_code():
    data = request.get_json()
    otp = data.get('otp')
    email = session.get('auth_flow_email')
    if not otp or not email:
        return jsonify({'success': False, 'message': 'OTP and email are required.'}), 400
    is_valid, message = verify_otp(email, otp)
    if is_valid:
        session['otp_verified'] = True
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@auth_bp.route('/complete_registration', methods=['POST'])
def complete_registration():
    if not session.get('otp_verified'):
        return jsonify({'success': False, 'message': 'OTP not verified.'}), 403

    data = request.get_json()
    password = data.get('password')
    name = data.get('name')
    email = session.get('auth_flow_email')

    if not all([password, name, email]):
        return jsonify({'success': False, 'message': 'Missing required information.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'This email has already been registered.'}), 409

    try:
        new_user = User(email=email, name=name, provider='email')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session.pop('auth_flow_email', None)
        session.pop('otp_verified', None)

        login_user(new_user)
        return jsonify({'success': True, 'redirect_url': url_for('profile.setup')})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User registration failed: {e}")
        return jsonify({'success': False, 'message': 'An internal error occurred.'}), 500

# --- Social Login and Other Routes (Unchanged) ---

@auth_bp.route('/google/login')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        email = user_info['email']
        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(
                email=email,
                name=user_info['name'],
                profile_pic_url=user_info['picture'],
                provider='google'
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return redirect(url_for('routes.dashboard'))
    except Exception as e:
        flash('An error occurred during Google login. Please try again.', 'danger')
        current_app.logger.error(f"Google callback failed: {e}")
        return redirect(url_for('auth.login'))

@auth_bp.route('/facebook/login')
def facebook_login():
    redirect_uri = url_for('auth.facebook_callback', _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)

@auth_bp.route('/facebook/callback')
def facebook_callback():
    try:
        token = oauth.facebook.authorize_access_token()
        user_info = oauth.facebook.get('me?fields=id,name,email,picture').json()
        email = user_info.get('email')

        if not email:
            flash('Facebook login failed. Your email is not public.', 'danger')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(
                email=email,
                name=user_info.get('name'),
                profile_pic_url=user_info.get('picture', {}).get('data', {}).get('url'),
                provider='facebook'
            )
            db.session.add(user)
            db.session.commit()
            
        login_user(user)
        return redirect(url_for('routes.dashboard'))
    except Exception as e:
        flash('An error occurred during Facebook login. Please try again.', 'danger')
        current_app.logger.error(f"Facebook callback failed: {e}")
        return redirect(url_for('auth.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        user = User.query.filter_by(email=email, provider='email').first()
        if not user:
            return jsonify({'success': False, 'message': 'No account with that email was found.'}), 404
        try:
            otp = generate_otp(email)
            if send_otp_email(email, otp):
                session['password_reset_email'] = email
                return jsonify({'success': True, 'message': 'An OTP has been sent to your email.'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP email.'}), 500
        except Exception as e:
            current_app.logger.error(f"Forgot password OTP sending failed: {e}")
            return jsonify({'success': False, 'message': 'An internal error occurred.'}), 500
    return render_template('forgot_password.html')

@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    otp = data.get('otp')
    password = data.get('password')
    email = session.get('password_reset_email')
    if not all([otp, password, email]):
        return jsonify({'success': False, 'message': 'Session expired or invalid request.'}), 400
    is_valid, message = verify_otp(email, otp)
    if not is_valid:
        return jsonify({'success': False, 'message': message}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404
    try:
        user.set_password(password)
        db.session.commit()
        session.pop('password_reset_email', None)
        return jsonify({'success': True, 'redirect_url': url_for('auth.login')})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset failed: {e}")
        return jsonify({'success': False, 'message': 'An internal error occurred.'}), 500

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.home'))
