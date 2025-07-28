# models/user_models.py
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db

# ... (user_streams and BroadcastNotificationView are unchanged) ...
user_streams = db.Table('user_streams',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('stream_id', db.Integer, db.ForeignKey('stream.id'), primary_key=True)
)

class BroadcastNotificationView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notification_id = db.Column(db.Integer, db.ForeignKey('notification.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'notification_id', name='_user_notification_view_uc'),)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    school = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    profile_pic_url = db.Column(db.String(200), nullable=True, default='https://placehold.co/100x100/A0AEC0/FFFFFF?text=User')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    provider = db.Column(db.String(20), nullable=False, default='email')

    streams = db.relationship('Stream', secondary=user_streams, lazy='subquery',
        backref=db.backref('users', lazy=True))

    notes = db.relationship('Note', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    saved_questions = db.relationship('SavedQuestion', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    reported_questions = db.relationship('ReportedQuestion', backref='reporter', lazy='dynamic', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    news_votes = db.relationship('NewsVote', backref='voter', lazy='dynamic', cascade="all, delete-orphan")
    read_broadcast_notifications = db.relationship('BroadcastNotificationView', backref='viewer', lazy='dynamic', cascade="all, delete-orphan")
    
    # --- NEW: Relationship to chat history ---
    chat_history = db.relationship('ChatHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

# ... (Notification, NoteImage, Note, ReportedQuestion, SavedQuestion are unchanged) ...
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class NoteImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    images = db.relationship('NoteImage', backref='note', lazy='dynamic', cascade="all, delete-orphan")

class ReportedQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_reason = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)

class SavedQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('question_id', 'user_id', name='_user_saved_question_uc'),)


# --- NEW: Model for storing chat history ---
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
