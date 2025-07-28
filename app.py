# app.py
import os
import datetime
from flask import Flask, redirect, url_for, request
from flask_login import current_user
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables from .env file
load_dotenv()

from extensions import db, login_manager, oauth
from models import * # Import all models from the new package

# Import blueprints
from auth import auth_bp
from routes import routes_bp
from user_profile import profile_bp
from admin import admin_bp
from history import history_bp
from notes import notes_bp
from notifications import notifications_bp
from news import news_bp
from interactions import interactions_bp
from gemini_ai import gemini_bp

app = Flask(__name__)

# --- Configurations (now loaded from .env) ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_fallback_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///question_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['FACEBOOK_CLIENT_ID'] = os.getenv('FACEBOOK_CLIENT_ID')
app.config['FACEBOOK_CLIENT_SECRET'] = os.getenv('FACEBOOK_CLIENT_SECRET')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('Question Bank', app.config['MAIL_USERNAME'])

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager.init_app(app)
oauth.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = "Please log in to access this page."

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_global_vars():
    if current_user.is_authenticated:
        user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
        broadcast_notifications = Notification.query.filter_by(user_id=None).order_by(Notification.timestamp.desc()).all()
        all_notifications = sorted(user_notifications + broadcast_notifications, key=lambda x: x.timestamp, reverse=True)
        
        unread_user_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
        read_broadcast_ids = db.session.query(BroadcastNotificationView.notification_id).filter_by(user_id=current_user.id).subquery()
        unread_broadcast_count = db.session.query(Notification.id).filter(
            Notification.user_id.is_(None),
            Notification.id.notin_(read_broadcast_ids)
        ).count()

        total_unread = unread_user_count + unread_broadcast_count
        
        return {
            'now': datetime.datetime.now,
            'notifications': all_notifications,
            'unread_notification_count': total_unread
        }
    return {'now': datetime.datetime.now}

@app.before_request
def before_request_handler():
    # This block ensures the database is created and seeded only once per application run.
    if not hasattr(app, 'tables_created'):
        with app.app_context():
            db.create_all()
            if Level.query.count() == 0:
                ssc = Level(name='SSC')
                hsc = Level(name='HSC')
                admission = Level(name='Admission')
                db.session.add_all([ssc, hsc, admission])
                db.session.commit()
                science = Stream(name='Science', level=ssc)
                arts = Stream(name='Arts', level=ssc)
                hsc_science = Stream(name='Science', level=hsc)
                admission_eng = Stream(name='Engineering', level=admission)
                db.session.add_all([science, arts, hsc_science, admission_eng])
                db.session.commit()
                dhaka_board = Board(name='Dhaka Board', tag='DB', stream=science)
                buet = Board(name='BUET', tag='BUET', stream=admission_eng)
                db.session.add_all([dhaka_board, buet])
                db.session.commit()
                physics = Subject(name='Physics', board=dhaka_board)
                math = Subject(name='Math', board=buet)
                db.session.add_all([physics, math])
                db.session.commit()
                vectors = Chapter(name='Vectors', subject=physics)
                calculus = Chapter(name='Calculus', subject=math)
                db.session.add_all([vectors, calculus])
                db.session.commit()
                dot_product = Topic(name='Dot Product', chapter=vectors)
                limits = Topic(name='Limits', chapter=calculus)
                db.session.add_all([dot_product, limits])
                db.session.commit()
        app.tables_created = True

    # This block forces new users to the setup page.
    if current_user.is_authenticated and not current_user.is_admin:
        if not current_user.streams:
            # Define the endpoints they ARE allowed to visit
            allowed_endpoints = ['profile.setup', 'auth.get_streams', 'auth.logout', 'static']
            
            # If the requested endpoint is NOT in the allowed list, redirect.
            if request.endpoint not in allowed_endpoints:
                return redirect(url_for('profile.setup'))

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(routes_bp, url_prefix='/')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(history_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(news_bp)
app.register_blueprint(interactions_bp)
app.register_blueprint(gemini_bp)

if __name__ == '__main__':
    app.run(debug=True)
