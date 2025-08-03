# interactions.py
import datetime
from flask import Blueprint, jsonify, request, render_template_string, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Question, SavedQuestion, ReportedQuestion, User
from decorators import check_access

interactions_bp = Blueprint('interactions', __name__)

@interactions_bp.route('/get_solution/<int:question_id>')
@login_required
def get_solution(question_id):
    """
    Checks user's access and returns the solution ONLY for an MCQ question.
    """
    question = Question.query.get_or_404(question_id)
    if question.question_type != 'MCQ':
        return jsonify({'status': 'error', 'message': 'Invalid question type for this endpoint.'}), 400

    user = User.query.get(current_user.id)
    is_premium = user.subscription_expiry and user.subscription_expiry > datetime.datetime.utcnow()

    if not user.is_admin and not is_premium:
        if user.mcq_views_left <= 0:
            return jsonify({
                'status': 'limit_reached', 
                'redirect_url': url_for('payments.pricing_page')
            }), 403
        user.mcq_views_left -= 1
        db.session.commit()

    solution_html = render_template_string(
        """
        <h3 class="text-lg font-semibold mb-2 text-gray-200">Solution:</h3>
        {% if question.solution_image_url %}
            <img src="{{ question.solution_image_url }}" alt="Solution Image" class="max-w-full h-auto mb-2 rounded-lg">
        {% endif %}
        <p class="text-gray-300">{{ question.solution | safe }}</p>
        """, question=question)
    return jsonify({'status': 'success', 'html': solution_html, 'correct_answer': question.correct_answer})

# --- ADDED: New dedicated route for CQ sub-answers ---
@interactions_bp.route('/get_cq_sub_answer/<int:question_id>/<string:sub_question_char>')
@login_required
def get_cq_sub_answer(question_id, sub_question_char):
    """
    Checks user's access and returns a single sub-answer for a CQ question.
    """
    question = Question.query.get_or_404(question_id)
    if question.question_type != 'CQ':
        return jsonify({'status': 'error', 'message': 'Invalid question type.'}), 400

    user = User.query.get(current_user.id)
    is_premium = user.subscription_expiry and user.subscription_expiry > datetime.datetime.utcnow()

    if not user.is_admin and not is_premium:
        if user.cq_views_left <= 0:
            return jsonify({
                'status': 'limit_reached',
                'redirect_url': url_for('payments.pricing_page')
            }), 403
        # Decrement the counter only when the first sub-question ('a') is requested
        if sub_question_char == 'a':
            user.cq_views_left -= 1
            db.session.commit()

    # Dynamically get the answer text and image url based on the character (a, b, c, d)
    answer_text = getattr(question, f"answer_{sub_question_char}", "")
    answer_image_url = getattr(question, f"answer_{sub_question_char}_image_url", None)

    answer_html = render_template_string(
        """
        <div class="text-gray-300">
            {{ answer_text | safe }}
            {% if answer_image_url %}
                <img src="{{ answer_image_url }}" alt="Sub-answer image" class="max-w-md h-auto my-2 rounded-lg">
            {% endif %}
        </div>
        """, answer_text=answer_text, answer_image_url=answer_image_url)
        
    return jsonify({'status': 'success', 'html': answer_html})

@interactions_bp.route('/save_question/<int:question_id>', methods=['POST'])
@login_required
def save_question(question_id):
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