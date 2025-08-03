# routes.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Question, Level, Stream, Board, SavedQuestion, ExamSession
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

    # --- ADDED: Calculate total study time ---
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
@routes_bp.route('/browse')
@login_required
def browse_levels():
    levels = Level.query.order_by(Level.name).all()
    return render_template('browse_levels.html', levels=levels)

@routes_bp.route('/browse/level/<int:level_id>')
@login_required
def browse_streams(level_id):
    level = Level.query.get_or_404(level_id)
    streams = Stream.query.filter_by(level_id=level.id).order_by(Stream.name).all()
    return render_template('browse_streams.html', level=level, streams=streams)

@routes_bp.route('/browse/stream/<int:stream_id>')
@login_required
def browse_boards(stream_id):
    stream = Stream.query.get_or_404(stream_id)
    boards = Board.query.filter_by(stream_id=stream.id).order_by(Board.name).all()
    return render_template('browse_boards.html', stream=stream, boards=boards)

@routes_bp.route('/browse/board/<int:board_id>/<string:question_type>')
@login_required
def view_board_questions(board_id, question_type):
    if question_type.upper() not in ['MCQ', 'CQ']:
        flash('Invalid question type selected.', 'danger')
        return redirect(url_for('routes.browse_levels'))

    board = Board.query.get_or_404(board_id)
    questions = Question.query.filter(
        Question.board_id == board_id,
        Question.question_type == question_type.upper()
    ).order_by(Question.year.desc(), Question.id).all()

    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    for q in questions:
        q.is_saved = q.id in saved_question_ids

    return render_template('view_board_questions.html',
                           board=board,
                           questions=questions,
                           question_type=question_type.upper())
