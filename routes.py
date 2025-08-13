# routes.py
import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from models import Question, Level, Stream, Board, SavedQuestion, ExamSession, Subject
from extensions import db
from sqlalchemy import func

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def home():
    return render_template('home.html')

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    user_stream_ids = [stream.id for stream in current_user.streams]
    
    question_query = Question.query
    if user_stream_ids:
        question_query = question_query.filter(Question.stream_id.in_(user_stream_ids))

    total_questions = question_query.count()
    total_mcqs = question_query.filter(Question.question_type == 'MCQ').count()
    total_cqs = question_query.filter(Question.question_type == 'CQ').count()

    total_seconds = db.session.query(func.sum(ExamSession.time_taken_seconds)).filter_by(user_id=current_user.id).scalar() or 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    study_time_str = f"{hours}h {minutes}m"

    return render_template('dashboard.html',
                           total_questions=total_questions,
                           total_mcqs=total_mcqs,
                           total_cqs=total_cqs,
                           study_time=study_time_str)

# --- Browsing structure ---
@routes_bp.route('/Question-bank')
@login_required
def browse_levels():
    levels = Level.query.order_by(Level.name).all()
    return render_template('browse_levels.html', levels=levels)

@routes_bp.route('/Question-bank/<string:level_name>')
@login_required
def browse_streams(level_name):
    level = Level.query.filter_by(name=level_name).first_or_404()
    streams = Stream.query.filter_by(level_id=level.id).order_by(Stream.name).all()
    return render_template('browse_streams.html', level=level, streams=streams)

@routes_bp.route('/Question-bank/<string:level_name>/<string:stream_name>')
@login_required
def browse_boards_by_name(level_name, stream_name):
    level = Level.query.filter_by(name=level_name).first_or_404()
    stream = Stream.query.filter_by(name=stream_name, level=level).first_or_404()
    boards = Board.query.filter_by(stream_id=stream.id).order_by(Board.name).all()
    return render_template('browse_boards.html', stream=stream, boards=boards)

@routes_bp.route('/Question-bank/<string:level_name>/<string:stream_name>/<string:board_name>')
@login_required
def browse_years(level_name, stream_name, board_name):
    level = Level.query.filter_by(name=level_name).first_or_404()
    stream = Stream.query.filter_by(name=stream_name, level=level).first_or_404()
    board = Board.query.filter_by(name=board_name, stream=stream).first_or_404()
    
    # Query distinct years for which questions exist for this board
    years_query = db.session.query(Question.year).filter_by(board_id=board.id).distinct().order_by(Question.year.desc())
    years = [y[0] for y in years_query]
    
    return render_template('browse_years.html', board=board, years=years)

@routes_bp.route('/Question-bank/<string:level_name>/<string:stream_name>/<string:board_name>/<int:year>')
@login_required
def browse_subjects_by_year(level_name, stream_name, board_name, year):
    level = Level.query.filter_by(name=level_name).first_or_404()
    stream = Stream.query.filter_by(name=stream_name, level=level).first_or_404()
    board = Board.query.filter_by(name=board_name, stream=stream).first_or_404()

    # Find subjects that have questions for the selected board and year
    subjects = Subject.query.filter(
        Subject.board_id == board.id,
        Subject.questions.any(Question.year == year)
    ).order_by(Subject.name).all()

    return render_template('browse_subjects.html', board=board, subjects=subjects, year=year)

@routes_bp.route('/Question-bank/<string:level_name>/<string:stream_name>/<string:board_name>/<int:year>/<string:subject_name>/<string:question_type>')
@login_required
def view_subject_questions_by_year(level_name, stream_name, board_name, year, subject_name, question_type):
    if question_type.upper() not in ['MCQ', 'CQ']:
        flash('Invalid question type selected.', 'danger')
        return redirect(url_for('routes.browse_levels'))

    level = Level.query.filter_by(name=level_name).first_or_404()
    stream = Stream.query.filter_by(name=stream_name, level=level).first_or_404()
    board = Board.query.filter_by(name=board_name, stream=stream).first_or_404()
    subject = Subject.query.filter_by(name=subject_name, board=board).first_or_404()

    page = request.args.get('page', 1, type=int)
    per_page = 50

    questions_pagination = Question.query.filter(
        Question.subject_id == subject.id,
        Question.year == year,
        Question.question_type == question_type.upper()
    ).order_by(Question.id).paginate(page=page, per_page=per_page, error_out=False)

    questions = questions_pagination.items

    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    for q in questions:
        q.is_saved = q.id in saved_question_ids

    is_premium = current_user.is_admin or (current_user.subscription_expiry and current_user.subscription_expiry > datetime.datetime.utcnow())

    return render_template('view_subject_questions.html',
                           subject=subject,
                           year=year,
                           questions=questions,
                           question_type=question_type.upper(),
                           is_premium=is_premium,
                           pagination=questions_pagination)


# --- API endpoint for infinite scroll ---
@routes_bp.route('/api/more_questions/<int:subject_id>/<string:question_type>/<int:year>')
@login_required
def get_more_questions(subject_id, question_type, year):
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    questions_pagination = Question.query.filter(
        Question.subject_id == subject_id,
        Question.year == year,
        Question.question_type == question_type.upper()
    ).order_by(Question.id).paginate(page=page, per_page=per_page, error_out=False)
    
    questions = questions_pagination.items

    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    for q in questions:
        q.is_saved = q.id in saved_question_ids

    is_premium = current_user.is_admin or (current_user.subscription_expiry and current_user.subscription_expiry > datetime.datetime.utcnow())

    html = render_template(
        'partials/_question_list.html',
        questions=questions,
        is_premium=is_premium,
        loop_offset=(page - 1) * per_page
    )

    return jsonify({
        'html': html,
        'has_next': questions_pagination.has_next
    })