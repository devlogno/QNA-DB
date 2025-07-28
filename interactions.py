# interactions.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
# --- UPDATED: Import 'db' from extensions, and models from 'models' ---
from extensions import db
from models import Question, SavedQuestion, ReportedQuestion

interactions_bp = Blueprint('interactions', __name__)

@interactions_bp.route('/save_question/<int:question_id>', methods=['POST'])
@login_required
def save_question(question_id):
    """Endpoint to save or unsave a question."""
    question = Question.query.get_or_404(question_id)
    saved_q = SavedQuestion.query.filter_by(user_id=current_user.id, question_id=question.id).first()

    if saved_q:
        db.session.delete(saved_q)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'unsaved', 'message': 'Question unsaved.'})
    else:
        new_saved_q = SavedQuestion(user_id=current_user.id, question_id=question.id)
        db.session.add(new_saved_q)
        db.session.commit()
        return jsonify({'status': 'success', 'action': 'saved', 'message': 'Question saved.'})

@interactions_bp.route('/report_question/<int:question_id>', methods=['POST'])
@login_required
def report_question(question_id):
    """Endpoint to report a question."""
    question = Question.query.get_or_404(question_id)
    reason = request.json.get('reason', 'No reason provided.')

    existing_report = ReportedQuestion.query.filter_by(
        question_id=question.id,
        reporter_id=current_user.id,
        is_resolved=False
    ).first()

    if existing_report:
        return jsonify({'status': 'info', 'message': 'You have already reported this question.'})
    else:
        new_report = ReportedQuestion(
            question_id=question.id,
            reporter_id=current_user.id,
            report_reason=reason
        )
        db.session.add(new_report)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Question reported to admin.'})
