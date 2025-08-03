# analytics.py
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import ExamSession, ExamAnswer, Subject, Question
from extensions import db
from sqlalchemy import func
import datetime

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@login_required
def performance_dashboard():
    """Displays the main performance analytics dashboard."""
    # Overall stats
    total_exams = ExamSession.query.filter_by(user_id=current_user.id).count()
    total_questions_answered = db.session.query(func.sum(ExamSession.total_questions)).filter_by(user_id=current_user.id).scalar() or 0
    
    # Accuracy by Subject
    accuracy_by_subject = db.session.query(
        Subject.name,
        func.avg(ExamAnswer.is_correct) * 100
    ).join(ExamAnswer.question).join(Question.subject).filter(
        ExamAnswer.exam_session.has(user_id=current_user.id)
    ).group_by(Subject.name).all()

    # Score history for chart
    score_history = ExamSession.query.filter_by(user_id=current_user.id).order_by(ExamSession.timestamp.asc()).all()
    
    # --- FIXED: Pre-format the data for the chart in the backend ---
    score_history_labels = [session.timestamp.strftime('%b %d') for session in score_history]
    score_history_data = [session.accuracy for session in score_history]
    
    return render_template(
        'analytics.html',
        total_exams=total_exams,
        total_questions_answered=total_questions_answered,
        accuracy_by_subject=accuracy_by_subject,
        score_history_labels=score_history_labels,
        score_history_data=score_history_data
    )

@analytics_bp.route('/study-calendar-data')
@login_required
def study_calendar_data():
    """Provides data for the study activity calendar."""
    one_year_ago = datetime.datetime.utcnow() - datetime.timedelta(days=365)
    
    study_sessions = db.session.query(
        func.date(ExamSession.timestamp),
        func.sum(ExamSession.time_taken_seconds)
    ).filter(
        ExamSession.user_id == current_user.id,
        ExamSession.timestamp >= one_year_ago
    ).group_by(func.date(ExamSession.timestamp)).all()
    
    # Format data for the calendar
    study_data = {date.strftime('%Y-%m-%d'): seconds for date, seconds in study_sessions}
    
    return jsonify(study_data)
