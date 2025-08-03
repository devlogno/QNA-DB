# quiz.py
import json
# --- MODIFIED: Added jsonify to the import statement ---
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.sql.expression import func
from models import Question, Subject, Chapter, Topic, ExamSession, ExamAnswer
from services.achievements_service import check_all_achievements
from extensions import db
from decorators import check_access

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

@quiz_bp.route('/create', methods=['GET', 'POST'])
@check_access(feature='exams')
def create_quiz():
    """Handles the creation of a custom quiz."""
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        chapter_id = request.form.get('chapter_id', type=int)
        topic_id = request.form.get('topic_id', type=int)
        complexity = request.form.get('complexity', type=int)
        num_questions = request.form.get('num_questions', type=int)
        time_limit = request.form.get('time_limit', type=int)
        question_type = request.form.get('question_type')

        if not all([subject_id, num_questions, time_limit, question_type]):
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('quiz.create_quiz'))

        query = Question.query.filter_by(question_type=question_type, subject_id=subject_id)
        if chapter_id:
            query = query.filter_by(chapter_id=chapter_id)
        if topic_id:
            query = query.filter_by(topic_id=topic_id)
        if complexity:
            query = query.filter(Question.complexity <= complexity)

        questions = query.order_by(func.random()).limit(num_questions).all()

        if not questions:
            flash('No questions found matching your criteria. Please try a broader search.', 'warning')
            return redirect(url_for('quiz.create_quiz'))

        # Create a new exam session
        exam = ExamSession(
            user_id=current_user.id,
            score=0, # Will be updated on submission
            total_questions=len(questions),
            time_taken_seconds=0, # Will be updated on submission
            settings={
                'subject_id': subject_id, 'chapter_id': chapter_id, 'topic_id': topic_id,
                'complexity': complexity, 'num_questions': num_questions, 
                'time_limit_minutes': time_limit, 'question_type': question_type
            }
        )
        db.session.add(exam)
        db.session.commit()

        return redirect(url_for('quiz.start_quiz', session_id=exam.id))

    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('quiz_create.html', subjects=subjects)

@quiz_bp.route('/session/<int:session_id>')
@login_required
def start_quiz(session_id):
    """Displays the quiz session page."""
    exam = ExamSession.query.get_or_404(session_id)
    if exam.user_id != current_user.id:
        flash('You are not authorized to take this exam.', 'danger')
        return redirect(url_for('routes.dashboard'))

    # Refetch questions based on the saved settings
    settings = exam.settings
    query = Question.query.filter_by(question_type=settings['question_type'], subject_id=settings['subject_id'])
    if settings.get('chapter_id'):
        query = query.filter_by(chapter_id=settings['chapter_id'])
    if settings.get('topic_id'):
        query = query.filter_by(topic_id=settings['topic_id'])
    
    questions = query.order_by(func.random()).limit(settings['num_questions']).all()
    
    return render_template('quiz_session.html', exam=exam, questions=questions)

@quiz_bp.route('/submit/<int:session_id>', methods=['POST'])
@login_required
def submit_quiz(session_id):
    """Handles quiz submission and calculates the score."""
    exam = ExamSession.query.get_or_404(session_id)
    if exam.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)
    
    score = 0
    question_ids = answers.keys()
    correct_answers = {str(q.id): q.correct_answer for q in Question.query.filter(Question.id.in_(question_ids)).all()}

    for q_id, user_answer in answers.items():
        is_correct = correct_answers.get(q_id) == user_answer
        if is_correct:
            score += 1
        
        new_answer = ExamAnswer(
            exam_session_id=exam.id,
            question_id=int(q_id),
            user_answer=user_answer,
            is_correct=is_correct
        )
        db.session.add(new_answer)

    # Update exam session
    exam.score = score
    exam.time_taken_seconds = time_taken
    
    # Award points
    current_user.points += score # 1 point per correct answer
    
    db.session.commit()
    
    # Check for achievements
    check_all_achievements(current_user)

    return jsonify({'success': True, 'redirect_url': url_for('quiz.quiz_results', session_id=exam.id)})

@quiz_bp.route('/results/<int:session_id>')
@login_required
def quiz_results(session_id):
    """Displays the results of a completed quiz."""
    exam = ExamSession.query.get_or_404(session_id)
    if exam.user_id != current_user.id:
        return redirect(url_for('routes.dashboard'))
        
    return render_template('quiz_results.html', exam=exam)
