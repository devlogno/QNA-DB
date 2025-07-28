# history.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import SavedQuestion, ReportedQuestion

history_bp = Blueprint('history', __name__)

@history_bp.route('/history')
@login_required
def saved_questions():
    """
    Displays the list of questions saved by the current user.
    This is the default view for the history section.
    """
    saved_entries = SavedQuestion.query.filter_by(user_id=current_user.id).order_by(SavedQuestion.timestamp.desc()).all()
    questions = [entry.question for entry in saved_entries]

    # Mark all questions as saved for the purpose of the template macro
    for q in questions:
        q.is_saved = True

    return render_template(
        'history.html', 
        questions=questions, 
        title="Your Saved Questions",
        active_view='saved'
    )

@history_bp.route('/history/reported')
@login_required
def reported_questions():
    """
    Displays the list of questions reported by the user that are not yet resolved.
    """
    reported_entries = ReportedQuestion.query.filter_by(
        reporter_id=current_user.id, 
        is_resolved=False
    ).order_by(ReportedQuestion.timestamp.desc()).all()
    
    questions = [entry.question for entry in reported_entries]

    # Check the saved status for each question
    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    for q in questions:
        q.is_saved = q.id in saved_question_ids

    return render_template(
        'history.html', 
        questions=questions, 
        title="Your Reported Questions (Pending)",
        active_view='reported'
    )

@history_bp.route('/history/solved')
@login_required
def solved_reports():
    """
    Displays the list of questions reported by the user that have been resolved by an admin.
    """
    solved_entries = ReportedQuestion.query.filter_by(
        reporter_id=current_user.id, 
        is_resolved=True
    ).order_by(ReportedQuestion.timestamp.desc()).all()
    
    questions = [entry.question for entry in solved_entries]

    # Check the saved status for each question
    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    for q in questions:
        q.is_saved = q.id in saved_question_ids

    return render_template(
        'history.html', 
        questions=questions, 
        title="Your Solved Reports",
        active_view='solved'
    )
