# models/gamification_models.py
import datetime
from extensions import db

# Association table for the many-to-many relationship between users and badges
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True),
    db.Column('awarded_at', db.DateTime, default=datetime.datetime.utcnow)
)

class Badge(db.Model):
    """
    Defines all possible badges that can be awarded to users.
    This table can be pre-populated with achievements.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon_svg = db.Column(db.Text, nullable=False)  # Storing SVG directly for flexibility
    criteria_value = db.Column(db.Integer, nullable=True) # e.g., number of questions for a badge

