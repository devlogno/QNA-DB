# history.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import SavedQuestion

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
@login_required
def saved_questions_history():
    """
    Displays the list of questions saved by the current user.
    """
    # Fetch all saved question records for the current user, ordered by when they were saved
    saved_entries = SavedQuestion.query.filter_by(user_id=current_user.id).order_by(SavedQuestion.timestamp.desc()).all()

    # Extract the actual Question objects from the saved entries
    questions = [entry.question for entry in saved_entries]

    # Mark all questions as saved for the purpose of the history page
    for q in questions:
        q.is_saved = True

    return render_template('history.html', questions=questions)
