# app.py
import os
import datetime
from flask import Flask, redirect, url_for, request
from flask_login import current_user
from dotenv import load_dotenv
from flask_migrate import Migrate
from sqlalchemy import select
import click

# Import extensions but do not initialize them
from extensions import db, login_manager, oauth, socketio

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    # --- Load Configurations ---
    load_dotenv()
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')
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

    # --- Initialize Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)
    socketio.init_app(app)
    Migrate(app, db)

    # --- Import and Register Blueprints ---
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
    from doubts import doubts_bp
    from user_routes import user_bp # --- NEW ---

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
    app.register_blueprint(doubts_bp, url_prefix='/doubts')
    app.register_blueprint(user_bp) # --- CORRECTED: This line was missing ---

    # --- Import Models within App Context ---
    from models import User, Notification, BroadcastNotificationView, Level, Stream, Board, Subject, Chapter, Topic, generate_public_id

    # --- Configure Flask-Login ---
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Please log in to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Context Processors and Request Hooks ---
    @app.context_processor
    def inject_global_vars():
        if current_user.is_authenticated:
            user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
            broadcast_notifications = Notification.query.filter_by(user_id=None).order_by(Notification.timestamp.desc()).all()
            all_notifications = sorted(user_notifications + broadcast_notifications, key=lambda x: x.timestamp, reverse=True)
            
            unread_user_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            
            read_broadcast_ids_stmt = select(BroadcastNotificationView.notification_id).where(BroadcastNotificationView.user_id == current_user.id)
            unread_broadcast_count = db.session.query(Notification.id).filter(
                Notification.user_id.is_(None),
                Notification.id.notin_(read_broadcast_ids_stmt)
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
        if not hasattr(app, 'tables_created'):
            with app.app_context():
                db.create_all()
                # Seeding logic...
            app.tables_created = True

        if current_user.is_authenticated and not current_user.is_admin:
            if not current_user.streams:
                allowed_endpoints = ['profile.setup', 'auth.get_streams', 'auth.logout', 'static']
                if request.endpoint not in allowed_endpoints:
                    return redirect(url_for('profile.setup'))

    # --- NEW: CLI Command to backfill public_ids for existing users ---
    @app.cli.command("backfill-public-ids")
    def backfill_public_ids():
        """Generate public_id for any users that don't have one."""
        users_without_id = User.query.filter(User.public_id.is_(None)).all()
        if not users_without_id:
            print("All users already have a public_id.")
            return

        for user in users_without_id:
            user.public_id = generate_public_id()
            print(f"Generated ID for {user.email}: {user.public_id}")

        db.session.commit()
        print(f"Successfully updated {len(users_without_id)} users.")

    return app

# --- Create and Run the App ---
app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)
