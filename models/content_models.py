# models/content_models.py
import datetime
from extensions import db

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    level_id = db.Column(db.Integer, db.ForeignKey('level.id'), nullable=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('stream.id'), nullable=True)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    votes = db.relationship('NewsVote', backref='article', lazy='dynamic', cascade="all, delete-orphan")

class NewsVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('news_article.id'), nullable=False)
    vote_type = db.Column(db.SmallInteger, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='_user_article_vote_uc'),)
