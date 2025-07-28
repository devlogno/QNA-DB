# models.py
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from extensions import db
from flask_login import UserMixin

# --- Association table for User <-> Stream ---
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

# --- Hierarchical Category Models (unchanged) ---
class Level(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    streams = db.relationship('Stream', backref='level', lazy='dynamic', cascade="all, delete-orphan")

class Stream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=False)
    boards = db.relationship('Board', backref='stream', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('name', 'level_id', name='_stream_level_uc'),)

class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(20), nullable=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=False)
    subjects = db.relationship('Subject', backref='board', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('name', 'stream_id', name='_board_stream_uc'),)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=False)
    chapters = db.relationship('Chapter', backref='subject', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('name', 'board_id', name='_subject_board_uc'),)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    topics = db.relationship('Topic', backref='chapter', lazy='dynamic', cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('name', 'subject_id', name='_chapter_subject_uc'),)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('name', 'chapter_id', name='_topic_chapter_uc'),)


# --- Core Application Models ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # --- NEW: school column added ---
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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

# ... (Rest of models are unchanged) ...
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    question_image_url = db.Column(db.String(200), nullable=True)
    question_type = db.Column(db.String(10), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    complexity = db.Column(db.Integer, nullable=False, default=5)
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=False)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=True)
    level = db.relationship('Level', backref='questions')
    stream = db.relationship('Stream', backref='questions')
    board = db.relationship('Board', backref='questions')
    subject = db.relationship('Subject', backref='questions')
    chapter = db.relationship('Chapter', backref='questions')
    topic = db.relationship('Topic', backref='questions')
    option_a = db.Column(db.Text, nullable=True)
    option_a_image_url = db.Column(db.String(200), nullable=True)
    option_b = db.Column(db.Text, nullable=True)
    option_b_image_url = db.Column(db.String(200), nullable=True)
    option_c = db.Column(db.Text, nullable=True)
    option_c_image_url = db.Column(db.String(200), nullable=True)
    option_d = db.Column(db.Text, nullable=True)
    option_d_image_url = db.Column(db.String(200), nullable=True)
    correct_answer = db.Column(db.String(1), nullable=True)
    question_a = db.Column(db.Text, nullable=True)
    answer_a = db.Column(db.Text, nullable=True)
    question_b = db.Column(db.Text, nullable=True)
    answer_b = db.Column(db.Text, nullable=True)
    question_c = db.Column(db.Text, nullable=True)
    answer_c = db.Column(db.Text, nullable=True)
    question_d = db.Column(db.Text, nullable=True)
    answer_d = db.Column(db.Text, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    solution_image_url = db.Column(db.String(200), nullable=True)
    reports = db.relationship('ReportedQuestion', backref='question', lazy='dynamic', cascade="all, delete-orphan")
    saved_by = db.relationship('SavedQuestion', backref='question', lazy='dynamic', cascade="all, delete-orphan")
    question_a_image_url = db.Column(db.String(200), nullable=True)
    answer_a_image_url = db.Column(db.String(200), nullable=True)
    question_b_image_url = db.Column(db.String(200), nullable=True)
    answer_b_image_url = db.Column(db.String(200), nullable=True)
    question_c_image_url = db.Column(db.String(200), nullable=True)
    answer_c_image_url = db.Column(db.String(200), nullable=True)
    question_d_image_url = db.Column(db.String(200), nullable=True)
    answer_d_image_url = db.Column(db.String(200), nullable=True)

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    for_ssc = db.Column(db.Boolean, default=True, nullable=False)
    for_hsc = db.Column(db.Boolean, default=True, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    votes = db.relationship('NewsVote', backref='article', lazy='dynamic', cascade="all, delete-orphan")

class NewsVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('news_article.id'), nullable=False)
    vote_type = db.Column(db.SmallInteger, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='_user_article_vote_uc'),)

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
