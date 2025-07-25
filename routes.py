# routes.py
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import db, Question, Level, Stream, Board, Subject, Chapter, Topic, SavedQuestion

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def home():
    """Renders the home page."""
    return render_template('home.html')

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    """Renders the user dashboard."""
    user_level_names = [level.name for level in current_user.levels]
    question_query = Question.query
    if user_level_names:
        levels = Level.query.filter(Level.name.in_(user_level_names)).all()
        level_ids = [level.id for level in levels]
        if level_ids:
            question_query = question_query.filter(Question.level_id.in_(level_ids))

    total_questions = question_query.count()
    total_mcqs = question_query.filter(Question.question_type == 'MCQ').count()
    total_cqs = question_query.filter(Question.question_type == 'CQ').count()

    solved_questions = 0
    new_questions_added = 0
    study_time = "0h 0m"

    return render_template('dashboard.html',
                           total_questions=total_questions,
                           total_mcqs=total_mcqs,
                           total_cqs=total_cqs,
                           solved_questions=solved_questions,
                           new_questions_added=new_questions_added,
                           study_time=study_time)

# --- New, Streamlined Browsing Structure ---

@routes_bp.route('/browse')
@login_required
def browse_levels():
    """Displays the top-level categories (Levels) for users to start browsing."""
    levels = Level.query.order_by(Level.name).all()
    return render_template('browse_levels.html', levels=levels)

@routes_bp.route('/browse/level/<int:level_id>')
@login_required
def browse_streams(level_id):
    """Displays the streams available under a selected level."""
    level = Level.query.get_or_404(level_id)
    streams = Stream.query.filter_by(level_id=level.id).order_by(Stream.name).all()
    return render_template('browse_streams.html', level=level, streams=streams)

@routes_bp.route('/browse/stream/<int:stream_id>')
@login_required
def browse_boards(stream_id):
    """Displays the boards available under a selected stream."""
    stream = Stream.query.get_or_404(stream_id)
    boards = Board.query.filter_by(stream_id=stream.id).order_by(Board.name).all()
    return render_template('browse_boards.html', stream=stream, boards=boards)

@routes_bp.route('/browse/board/<int:board_id>/<string:question_type>')
@login_required
def view_board_questions(board_id, question_type):
    """
    Displays all questions of a specific type (MCQ or CQ) for a given board.
    """
    if question_type.upper() not in ['MCQ', 'CQ']:
        flash('Invalid question type selected.', 'danger')
        return redirect(url_for('routes.browse_levels'))

    board = Board.query.get_or_404(board_id)
    
    questions = Question.query.filter(
        Question.board_id == board_id,
        Question.question_type == question_type.upper()
    ).order_by(Question.year.desc(), Question.id).all()

    # Check saved status for each question
    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    for q in questions:
        q.is_saved = q.id in saved_question_ids

    return render_template('view_board_questions.html',
                           board=board,
                           questions=questions,
                           question_type=question_type.upper())
