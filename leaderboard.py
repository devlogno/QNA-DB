# leaderboard.py
from flask import Blueprint, render_template
from flask_login import login_required
from models import User
from extensions import db

leaderboard_bp = Blueprint('leaderboard', __name__, url_prefix='/leaderboard')

@leaderboard_bp.route('/')
@login_required
def show_leaderboard():
    """Displays the all-time leaderboard."""
    top_users = User.query.order_by(User.points.desc()).limit(50).all()
    return render_template('leaderboard.html', users=top_users)

