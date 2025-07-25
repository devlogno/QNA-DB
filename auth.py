# auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from models import db, User, Level # Import Level model

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('routes.dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration with dynamic level selection."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Get list of selected level IDs from the form
        selected_level_ids = request.form.getlist('levels', type=int)

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
        elif not selected_level_ids:
            flash('Please select at least one level.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose a different one.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email or login.', 'danger')
        else:
            # Fetch the Level objects corresponding to the selected IDs
            selected_levels = Level.query.filter(Level.id.in_(selected_level_ids)).all()
            
            new_user = User(username=username, email=email, is_admin=False)
            new_user.set_password(password)
            
            # Assign the selected levels to the user
            new_user.levels = selected_levels
            
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        
        # If there was an error, re-render the form with the user's input
        all_levels = Level.query.order_by(Level.name).all()
        return render_template('register.html', 
                               levels=all_levels, 
                               username=username, 
                               email=email,
                               checked_levels=selected_level_ids)

    # For a GET request, just fetch the levels and render the form
    all_levels = Level.query.order_by(Level.name).all()
    return render_template('register.html', levels=all_levels, checked_levels=[])

@auth_bp.route('/logout')
def logout():
    """Logs out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.home'))
