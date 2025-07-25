# app.py
import os
import datetime
from flask import Flask
from flask_login import LoginManager, current_user
from models import db, User, Level, Stream, Board, Subject, Chapter, Topic, Note, Notification, NewsArticle, NewsVote

# Import blueprints
from auth import auth_bp
from routes import routes_bp
from profile import profile_bp
from admin import admin_bp
from history import history_bp
from notes import notes_bp
from notifications import notifications_bp
from news import news_bp
from interactions import interactions_bp # ADDED: Import the new blueprint

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your_strong_random_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///question_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_global_vars():
    if current_user.is_authenticated:
        user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
        broadcast_notifications = Notification.query.filter_by(user_id=None).order_by(Notification.timestamp.desc()).all()
        all_notifications = sorted(user_notifications + broadcast_notifications, key=lambda x: x.timestamp, reverse=True)
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        unread_broadcast_count = Notification.query.filter(Notification.user_id.is_(None), Notification.is_read == False).count()
        return {
            'now': datetime.datetime.now,
            'notifications': all_notifications,
            'unread_notification_count': unread_count + unread_broadcast_count
        }
    return {'now': datetime.datetime.now}

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(routes_bp, url_prefix='/')
app.register_blueprint(profile_bp, url_prefix='/')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(history_bp, url_prefix='/')
app.register_blueprint(notes_bp, url_prefix='/')
app.register_blueprint(notifications_bp, url_prefix='/')
app.register_blueprint(news_bp, url_prefix='/')
app.register_blueprint(interactions_bp, url_prefix='/') # ADDED: Register the new blueprint

@app.before_request
def create_tables_and_populate_data():
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

if __name__ == '__main__':
    app.run(debug=True)
