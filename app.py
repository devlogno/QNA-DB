# app.py
import os
import datetime
from flask import Flask, redirect, url_for, request
from flask_login import current_user
from dotenv import load_dotenv
from flask_migrate import Migrate
from sqlalchemy import select
import click

from extensions import db, login_manager, oauth, socketio

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

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

    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)
    socketio.init_app(app)
    Migrate(app, db)

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
    from user_routes import user_bp
    from api import api_bp
    from analytics import analytics_bp
    from leaderboard import leaderboard_bp
    from quiz import quiz_bp
    from payments import payments_bp

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
    app.register_blueprint(user_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(payments_bp)

    from models import User, Notification, BroadcastNotificationView, Level, Stream, Board, Subject, Chapter, Topic, generate_public_id, Badge

    # --- MODIFIED: Create database tables and seed initial data on startup ---
    with app.app_context():
        db.create_all()
        # Seed the database only if it's empty
        if Level.query.count() == 0:
            print("Seeding initial database categories...")
            ssc = Level(name='SSC')
            hsc = Level(name='HSC')
            admission = Level(name='Admission')
            
            science = Stream(name='Science', level=ssc)
            arts = Stream(name='Arts', level=ssc)
            hsc_science = Stream(name='Science', level=hsc)
            admission_eng = Stream(name='Engineering', level=admission)
            
            dhaka_board = Board(name='Dhaka Board', tag='DB', stream=science)
            buet = Board(name='BUET', tag='BUET', stream=admission_eng)
            
            physics = Subject(name='Physics', board=dhaka_board)
            math = Subject(name='Math', board=buet)
            
            vectors = Chapter(name='Vectors', subject=physics)
            calculus = Chapter(name='Calculus', subject=math)
            
            dot_product = Topic(name='Dot Product', chapter=vectors)
            limits = Topic(name='Limits', chapter=calculus)
            
            db.session.add_all([
                ssc, hsc, admission,
                science, arts, hsc_science, admission_eng,
                dhaka_board, buet,
                physics, math,
                vectors, calculus,
                dot_product, limits
            ])
            db.session.commit()
            print("Seeding complete.")


    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Please log in to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

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
        # --- MODIFIED: Removed database creation from here ---
        if current_user.is_authenticated and not current_user.is_admin:
            if not current_user.streams:
                allowed_endpoints = ['profile.setup', 'auth.get_streams', 'auth.logout', 'static']
                
                if request.endpoint not in allowed_endpoints:
                    return redirect(url_for('profile.setup'))

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

    @app.cli.command("seed-badges")
    def seed_badges():
        """Pre-populates the Badge table with achievements."""
        badges_to_add = [
            {'name': 'First Answer', 'description': 'Contribute your first answer in the community forum.', 'icon_svg': '<svg class="w-full h-full text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>'},
            {'name': 'Novice Solver', 'description': 'Solve 10 questions in practice quizzes.', 'icon_svg': '<svg class="w-full h-full text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'},
            {'name': 'Half-Century Solver', 'description': 'Solve 50 questions in practice quizzes.', 'icon_svg': '<svg class="w-full h-full text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path></svg>'},
            {'name': 'Century Solver', 'description': 'Solve 100 questions in practice quizzes.', 'icon_svg': '<svg class="w-full h-full text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-12v4m-2-2h4m5 4v4m-2-2h4M5 3a2 2 0 00-2 2v1m16 0V5a2 2 0 00-2-2h-1m-4 16l2 2l2-2m-4-4l2 2l2-2m-4 4V3"></path></svg>'}
        ]
        
        for badge_data in badges_to_add:
            badge = Badge.query.filter_by(name=badge_data['name']).first()
            if not badge:
                new_badge = Badge(**badge_data)
                db.session.add(new_badge)
                print(f"Added badge: {badge_data['name']}")
        
        db.session.commit()
        print("Badges seeded successfully.")

    return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)
