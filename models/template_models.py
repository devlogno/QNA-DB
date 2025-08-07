# models/template_models.py
from extensions import db

class SubjectTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True) # e.g., "HSC Physics Syllabus"
    chapters = db.relationship('ChapterTemplate', backref='subject_template', lazy='dynamic', cascade="all, delete-orphan")

class ChapterTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_template_id = db.Column(db.Integer, db.ForeignKey('subject_template.id'), nullable=False)
    topics = db.relationship('TopicTemplate', backref='chapter_template', lazy='dynamic', cascade="all, delete-orphan")

class TopicTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    chapter_template_id = db.Column(db.Integer, db.ForeignKey('chapter_template.id'), nullable=False)
