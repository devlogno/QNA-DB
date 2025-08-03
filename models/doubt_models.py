# models/doubt_models.py
import datetime
from extensions import db

class DoubtPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    
    # --- NEW: Add foreign keys for categorization ---
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)

    author = db.relationship("User", backref="doubt_posts")
    answers = db.relationship("DoubtAnswer", backref="post", lazy='dynamic', cascade="all, delete-orphan")
    images = db.relationship("PostImage", backref="post", lazy='dynamic', cascade="all, delete-orphan")
    
    # --- NEW: Add relationships to category models ---
    level = db.relationship('Level', backref='doubt_posts')
    stream = db.relationship('Stream', backref='doubt_posts')

class DoubtAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('doubt_post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('doubt_answer.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)

    author = db.relationship("User", backref="doubt_answers")
    images = db.relationship("PostImage", backref="answer", lazy='dynamic', cascade="all, delete-orphan")
    replies = db.relationship("DoubtAnswer", backref=db.backref('parent', remote_side=[id]), lazy='dynamic', cascade="all, delete-orphan")

class PostImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('doubt_post.id'), nullable=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('doubt_answer.id'), nullable=True)