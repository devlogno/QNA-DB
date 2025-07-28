# models/user_models.py
import datetime
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db

# --- NEW: Helper function to generate a unique public ID ---
def generate_public_id():
    # Loop to ensure the generated ID is unique
    while True:
        public_id = secrets.token_urlsafe(8)
        if not User.query.filter_by(public_id=public_id).first():
            return public_id

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
    # --- NEW: public_id for secure, anonymous profile URLs ---
    public_id = db.Column(db.String(12), unique=True, nullable=False, default=generate_public_id)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    school = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    profile_pic_url = db.Column(db.String(200), nullable=True, default='https://placehold.co/100x100/A0AEC0/FFFFFF?text=User')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    provider = db.Column(db.String(20), nullable=False, default='email')

    streams = db.relationship("Stream", secondary=user_streams, lazy='subquery',
        backref=db.backref('users', lazy=True))

    notes = db.relationship("Note", backref='author', lazy='dynamic', cascade="all, delete-orphan")
    saved_questions = db.relationship("SavedQuestion", backref='user', lazy='dynamic', cascade="all, delete-orphan")
    reported_questions = db.relationship("ReportedQuestion", backref='reporter', lazy='dynamic', cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref='user', lazy='dynamic', cascade="all, delete-orphan")
    news_votes = db.relationship("NewsVote", backref='voter', lazy='dynamic', cascade="all, delete-orphan")
    read_broadcast_notifications = db.relationship("BroadcastNotificationView", backref='viewer', lazy='dynamic', cascade="all, delete-orphan")
    chat_history = db.relationship("ChatHistory", backref='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

# --- NEW: Model for handling user reports ---
class UserReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)

    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='sent_reports')
    reported = db.relationship('User', foreign_keys=[reported_id], backref='received_reports')


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    link_url = db.Column(db.String(255), nullable=True)


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

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
