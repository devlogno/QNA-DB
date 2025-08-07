# quiz.py
import json
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.sql.expression import func
from sqlalchemy import case, or_
# --- MODIFIED: Added 'Board' to the import list ---
from models import Question, Subject, Chapter, Topic, ExamSession, ExamAnswer, Board
from services.achievements_service import check_all_achievements
from extensions import db
from decorators import check_access

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

@quiz_bp.route('/create', methods=['GET', 'POST'])
@check_access(feature='exams')
def create_quiz():
    """Handles the creation of a custom quiz."""
    if request.method == 'POST':
        data = request.form
        
        subject_ids = request.form.getlist('subject_ids', type=int)
        chapter_ids = request.form.getlist('chapter_ids', type=int)
        topic_ids = request.form.getlist('topic_ids', type=int)
        
        complexity = data.get('complexity', type=int)
        time_limit = data.get('time_limit', type=int)
        question_type = data.get('question_type')
        negative_marking = 'negative_marking' in data
        
        num_mcq = data.get('num_mcq', 0, type=int)
        num_cq = data.get('num_cq', 0, type=int)

        if not any([subject_ids, chapter_ids, topic_ids]):
            flash('You must select at least one subject, chapter, or topic.', 'danger')
            return redirect(url_for('quiz.create_quiz'))

        base_query = Question.query
        filters = []
        if topic_ids: filters.append(Question.topic_id.in_(topic_ids))
        if chapter_ids: filters.append(Question.chapter_id.in_(chapter_ids))
        if subject_ids: filters.append(Question.subject_id.in_(subject_ids))
        if filters: base_query = base_query.filter(or_(*filters))
        if complexity: base_query = base_query.filter(Question.complexity <= complexity)

        questions = []
        if question_type == 'MCQ' or question_type == 'Both':
            mcqs = base_query.filter_by(question_type='MCQ').order_by(func.random()).limit(num_mcq).all()
            questions.extend(mcqs)
        
        if question_type == 'CQ' or question_type == 'Both':
            cqs = base_query.filter_by(question_type='CQ').order_by(func.random()).limit(num_cq).all()
            questions.extend(cqs)

        if not questions:
            flash('No questions found matching your criteria. Please try a broader search.', 'warning')
            return redirect(url_for('quiz.create_quiz'))

        question_ids = [q.id for q in questions]

        exam = ExamSession(
            user_id=current_user.id,
            score=0,
            total_questions=len(questions),
            time_taken_seconds=0,
            question_ids_json=question_ids,
            settings={
                'subject_ids': subject_ids, 'chapter_ids': chapter_ids, 'topic_ids': topic_ids,
                'complexity': complexity, 'num_mcq': num_mcq, 'num_cq': num_cq,
                'time_limit_minutes': time_limit, 'question_type': question_type,
                'negative_marking': negative_marking
            }
        )
        db.session.add(exam)
        db.session.commit()

        return redirect(url_for('quiz.start_quiz', session_id=exam.id))

    # --- GET Request Logic ---
    user_stream_ids = [s.id for s in current_user.streams]
    user_subjects = Subject.query.join(Board).filter(Board.stream_id.in_(user_stream_ids)).order_by(Subject.name).all()

    return render_template('quiz_create.html', subjects=user_subjects)

@quiz_bp.route('/api/chapters_and_topics')
@login_required
def get_chapters_and_topics():
    subject_ids_str = request.args.get('subject_ids')
    if not subject_ids_str:
        return jsonify({'error': 'No subject_ids provided'}), 400
    
    subject_ids = [int(id) for id in subject_ids_str.split(',')]
    
    subjects_data = Subject.query.filter(Subject.id.in_(subject_ids)).all()
    
    response_data = []
    for subject in subjects_data:
        subject_dict = {
            'id': subject.id,
            'name': subject.name,
            'chapters': []
        }
        for chapter in subject.chapters:
            chapter_dict = {
                'id': chapter.id,
                'name': chapter.name,
                'topics': [{'id': topic.id, 'name': topic.name} for topic in chapter.topics]
            }
            subject_dict['chapters'].append(chapter_dict)
        response_data.append(subject_dict)
        
    return jsonify(response_data)


@quiz_bp.route('/session/<int:session_id>')
@login_required
def start_quiz(session_id):
    """Displays the quiz session page."""
    exam = ExamSession.query.get_or_404(session_id)
    if exam.user_id != current_user.id:
        flash('You are not authorized to take this exam.', 'danger')
        return redirect(url_for('routes.dashboard'))

    ordered_ids = exam.question_ids_json
    if not ordered_ids:
        flash('Could not load questions for this session. It may be an older exam.', 'danger')
        return redirect(url_for('routes.dashboard'))

    ordering = case({id: index for index, id in enumerate(ordered_ids)}, value=Question.id)
    questions = Question.query.filter(Question.id.in_(ordered_ids)).order_by(ordering).all()
    
    return render_template('quiz_session.html', exam=exam, questions=questions)

@quiz_bp.route('/submit/<int:session_id>', methods=['POST'])
@login_required
def submit_quiz(session_id):
    """Handles quiz submission and calculates the score."""
    exam = ExamSession.query.get_or_404(session_id)
    if exam.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    submitted_answers = data.get('answers', {})
    time_taken = data.get('time_taken', 0)
    
    # If it's a CQ-only exam, it's just for practice, not scoring.
    if exam.settings.get('question_type') == 'CQ':
        exam.time_taken_seconds = time_taken
        exam.score = 0
        db.session.commit()
        return jsonify({'success': True, 'redirect_url': url_for('quiz.quiz_results', session_id=exam.id)})

    score = 0
    all_question_ids = exam.question_ids_json
    questions_in_exam = Question.query.filter(Question.id.in_(all_question_ids)).all()
    questions_map = {q.id: q for q in questions_in_exam}

    negative_marking = exam.settings.get('negative_marking', False)
    
    for q_id in all_question_ids:
        question = questions_map.get(q_id)
        if not question or question.question_type != 'MCQ':
            continue

        user_answer = submitted_answers.get(str(q_id))
        correct_answer = question.correct_answer.strip() if question.correct_answer else None
        
        is_correct = (user_answer is not None) and (user_answer.lower() == correct_answer.lower())
        
        if is_correct:
            score += 1
        elif user_answer is not None and negative_marking:
            score -= 0.25 # Standard negative marking value

        new_answer_record = ExamAnswer(exam_session_id=exam.id, question_id=q_id, user_answer=user_answer, is_correct=is_correct)
        db.session.add(new_answer_record)

    exam.score = score
    exam.time_taken_seconds = time_taken
    current_user.points += max(0, score) # Don't award negative points overall
    
    db.session.commit()
    check_all_achievements(current_user)

    return jsonify({'success': True, 'redirect_url': url_for('quiz.quiz_results', session_id=exam.id)})

@quiz_bp.route('/results/<int:session_id>')
@login_required
def quiz_results(session_id):
    """Displays the results of a completed quiz."""
    exam = ExamSession.query.get_or_404(session_id)
    if exam.user_id != current_user.id:
        return redirect(url_for('routes.dashboard'))
        
    is_premium = current_user.is_admin or (current_user.subscription_expiry and current_user.subscription_expiry > datetime.datetime.utcnow())

    ordered_ids = exam.question_ids_json
    ordered_items = []
    if ordered_ids:
        # For scored exams, get the answers
        if exam.settings.get('question_type') != 'CQ':
            answers_map = {ans.question_id: ans for ans in exam.answers}
            ordered_items = [answers_map.get(qid) for qid in ordered_ids if answers_map.get(qid)]
        # For CQ practice, just get the questions
        else:
            ordering = case({id: index for index, id in enumerate(ordered_ids)}, value=Question.id)
            ordered_items = Question.query.filter(Question.id.in_(ordered_ids)).order_by(ordering).all()
    else:
        ordered_items = exam.answers.order_by(ExamAnswer.id).all()

    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    for item in ordered_items:
        question = item if isinstance(item, Question) else item.question
        if question:
            question.is_saved = question.id in saved_question_ids

    return render_template('quiz_results.html', exam=exam, is_premium=is_premium, items=ordered_items)
