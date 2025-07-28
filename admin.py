# admin.py
import os
import functools
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Question, ReportedQuestion, User, Notification, NewsArticle
from models import Level, Stream, Board, Subject, Chapter, Topic

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to ensure the user is an admin."""
    @login_required
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have administrative access.', 'danger')
            return redirect(url_for('routes.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def upload_file(file):
    """Helper function to save uploaded files and return their URL."""
    if file and file.filename != '':
        try:
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            return url_for('static', filename=f'uploads/{filename}')
        except Exception as e:
            print(f"Error uploading file: {e}")
            flash(f"Error uploading file: {file.filename}", "danger")
            return None
    return None

# --- Main Admin Routes ---

@admin_bp.route('/')
@admin_required
def admin_dashboard():
    total_questions = Question.query.count()
    total_reported = ReportedQuestion.query.filter_by(is_resolved=False).count()
    return render_template('admin_dashboard.html', total_questions=total_questions, total_reported=total_reported)

@admin_bp.route('/manage_categories')
@admin_required
def manage_categories():
    return render_template('admin_manage_categories.html')

@admin_bp.route('/add_question', methods=['GET', 'POST'])
@admin_required
def add_question():
    if request.method == 'POST':
        try:
            new_question = Question(
                question_type=request.form.get('question_type'),
                question_text=request.form.get('question_text'),
                year=int(request.form.get('year')),
                complexity=int(request.form.get('complexity')),
                solution=request.form.get('solution'),
                level_id=int(request.form.get('level_id')),
                stream_id=int(request.form.get('stream_id')) if request.form.get('stream_id') else None,
                board_id=int(request.form.get('board_id')) if request.form.get('board_id') else None,
                subject_id=int(request.form.get('subject_id')) if request.form.get('subject_id') else None,
                chapter_id=int(request.form.get('chapter_id')) if request.form.get('chapter_id') else None,
                topic_id=int(request.form.get('topic_id')) if request.form.get('topic_id') else None,
                question_image_url=upload_file(request.files.get('question_image')),
                solution_image_url=upload_file(request.files.get('solution_image'))
            )

            if new_question.question_type == 'MCQ':
                new_question.option_a = request.form.get('option_a')
                new_question.option_b = request.form.get('option_b')
                new_question.option_c = request.form.get('option_c')
                new_question.option_d = request.form.get('option_d')
                new_question.correct_answer = request.form.get('correct_answer')
                new_question.option_a_image_url = upload_file(request.files.get('option_a_image'))
                new_question.option_b_image_url = upload_file(request.files.get('option_b_image'))
                new_question.option_c_image_url = upload_file(request.files.get('option_c_image'))
                new_question.option_d_image_url = upload_file(request.files.get('option_d_image'))
            
            elif new_question.question_type == 'CQ':
                new_question.question_a = request.form.get('cq_question_a')
                new_question.answer_a = request.form.get('cq_answer_a')
                new_question.question_b = request.form.get('cq_question_b')
                new_question.answer_b = request.form.get('cq_answer_b')
                new_question.question_c = request.form.get('cq_question_c')
                new_question.answer_c = request.form.get('cq_answer_c')
                new_question.question_d = request.form.get('cq_question_d')
                new_question.answer_d = request.form.get('cq_answer_d')
                
                new_question.question_a_image_url = upload_file(request.files.get('cq_question_a_image'))
                new_question.answer_a_image_url = upload_file(request.files.get('cq_answer_a_image'))
                new_question.question_b_image_url = upload_file(request.files.get('cq_question_b_image'))
                new_question.answer_b_image_url = upload_file(request.files.get('cq_answer_b_image'))
                new_question.question_c_image_url = upload_file(request.files.get('cq_question_c_image'))
                new_question.answer_c_image_url = upload_file(request.files.get('cq_answer_c_image'))
                new_question.question_d_image_url = upload_file(request.files.get('cq_question_d_image'))
                new_question.answer_d_image_url = upload_file(request.files.get('cq_answer_d_image'))

            db.session.add(new_question)
            db.session.commit()
            flash(f'{new_question.question_type} question added successfully!', 'success')
            return redirect(url_for('admin.add_question'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            print(f"Error adding question: {e}")
    
    levels = Level.query.all()
    levels_data = [{'id': level.id, 'name': level.name} for level in levels]
    return render_template('admin_add_question.html', levels_data=levels_data)

@admin_bp.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        try:
            question.question_type = request.form.get('question_type')
            question.question_text = request.form.get('question_text')
            question.year = int(request.form.get('year'))
            question.complexity = int(request.form.get('complexity'))
            question.solution = request.form.get('solution')
            question.level_id = int(request.form.get('level_id'))
            question.stream_id = int(request.form.get('stream_id')) if request.form.get('stream_id') else None
            question.board_id = int(request.form.get('board_id')) if request.form.get('board_id') else None
            question.subject_id = int(request.form.get('subject_id')) if request.form.get('subject_id') else None
            question.chapter_id = int(request.form.get('chapter_id')) if request.form.get('chapter_id') else None
            question.topic_id = int(request.form.get('topic_id')) if request.form.get('topic_id') else None

            if 'question_image' in request.files and request.files['question_image'].filename != '':
                question.question_image_url = upload_file(request.files.get('question_image'))
            if 'solution_image' in request.files and request.files['solution_image'].filename != '':
                question.solution_image_url = upload_file(request.files.get('solution_image'))

            if question.question_type == 'MCQ':
                question.option_a = request.form.get('option_a')
                question.option_b = request.form.get('option_b')
                question.option_c = request.form.get('option_c')
                question.option_d = request.form.get('option_d')
                question.correct_answer = request.form.get('correct_answer')
                if 'option_a_image' in request.files and request.files['option_a_image'].filename != '':
                    question.option_a_image_url = upload_file(request.files.get('option_a_image'))
                if 'option_b_image' in request.files and request.files['option_b_image'].filename != '':
                    question.option_b_image_url = upload_file(request.files.get('option_b_image'))
                if 'option_c_image' in request.files and request.files['option_c_image'].filename != '':
                    question.option_c_image_url = upload_file(request.files.get('option_c_image'))
                if 'option_d_image' in request.files and request.files['option_d_image'].filename != '':
                    question.option_d_image_url = upload_file(request.files.get('option_d_image'))

            elif question.question_type == 'CQ':
                question.question_a = request.form.get('cq_question_a')
                question.answer_a = request.form.get('cq_answer_a')
                question.question_b = request.form.get('cq_question_b')
                question.answer_b = request.form.get('cq_answer_b')
                question.question_c = request.form.get('cq_question_c')
                question.answer_c = request.form.get('cq_answer_c')
                question.question_d = request.form.get('cq_question_d')
                question.answer_d = request.form.get('cq_answer_d')

                if 'cq_question_a_image' in request.files and request.files['cq_question_a_image'].filename != '':
                    question.question_a_image_url = upload_file(request.files.get('cq_question_a_image'))
                if 'cq_answer_a_image' in request.files and request.files['cq_answer_a_image'].filename != '':
                    question.answer_a_image_url = upload_file(request.files.get('cq_answer_a_image'))
                if 'cq_question_b_image' in request.files and request.files['cq_question_b_image'].filename != '':
                    question.question_b_image_url = upload_file(request.files.get('cq_question_b_image'))
                if 'cq_answer_b_image' in request.files and request.files['cq_answer_b_image'].filename != '':
                    question.answer_b_image_url = upload_file(request.files.get('cq_answer_b_image'))
                if 'cq_question_c_image' in request.files and request.files['cq_question_c_image'].filename != '':
                    question.question_c_image_url = upload_file(request.files.get('cq_question_c_image'))
                if 'cq_answer_c_image' in request.files and request.files['cq_answer_c_image'].filename != '':
                    question.answer_c_image_url = upload_file(request.files.get('cq_answer_c_image'))
                if 'cq_question_d_image' in request.files and request.files['cq_question_d_image'].filename != '':
                    question.question_d_image_url = upload_file(request.files.get('cq_question_d_image'))
                if 'cq_answer_d_image' in request.files and request.files['cq_answer_d_image'].filename != '':
                    question.answer_d_image_url = upload_file(request.files.get('cq_answer_d_image'))

            db.session.commit()
            flash('Question updated successfully!', 'success')
            return redirect(url_for('admin.reported_questions'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating the question: {str(e)}', 'danger')

    levels = Level.query.all()
    levels_data = [{'id': level.id, 'name': level.name} for level in levels]
    question_categories = {
        'level_id': question.level_id,
        'stream_id': question.stream_id,
        'board_id': question.board_id,
        'subject_id': question.subject_id,
        'chapter_id': question.chapter_id,
        'topic_id': question.topic_id,
    }
    return render_template('admin_edit_question.html',
                           question=question,
                           levels_data=levels_data,
                           question_categories=question_categories)

# --- News and Notification Routes ---
@admin_bp.route('/add_news', methods=['GET', 'POST'])
@admin_required
def add_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        for_ssc = 'for_ssc' in request.form
        for_hsc = 'for_hsc' in request.form
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('admin.add_news'))
            
        # --- UPDATED: Image handling logic for news ---
        image_url = None
        if 'image' in request.files and request.files['image'].filename != '':
            image_url = upload_file(request.files.get('image'))

        new_article = NewsArticle(
            title=title, 
            content=content, 
            for_ssc=for_ssc, 
            for_hsc=for_hsc,
            image_url=image_url
        )
        db.session.add(new_article)
        db.session.commit()
        flash('News article posted successfully!', 'success')
        return redirect(url_for('admin.admin_dashboard'))
        
    return render_template('admin_add_news.html')

@admin_bp.route('/send_notification', methods=['GET', 'POST'])
@admin_required
def send_notification():
    if request.method == 'POST':
        message = request.form.get('message')
        email = request.form.get('email') 
        if not message:
            flash('Notification message cannot be empty.', 'danger')
            return redirect(url_for('admin.send_notification'))
        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                notification = Notification(message=message, user_id=user.id)
                db.session.add(notification)
                db.session.commit()
                flash(f'Notification sent to {user.name or user.email}.', 'success')
            else:
                flash(f'User with email "{email}" not found.', 'danger')
        else:
            users = User.query.all()
            for user in users:
                notification = Notification(message=message, user_id=user.id)
                db.session.add(notification)
            db.session.commit()
            flash('Notification broadcast to all users.', 'success')
        return redirect(url_for('admin.send_notification'))
    return render_template('admin_send_notification.html')

# --- Reported Questions Routes ---
@admin_bp.route('/reported_questions')
@admin_required
def reported_questions():
    reports = ReportedQuestion.query.filter_by(is_resolved=False).order_by(ReportedQuestion.timestamp.desc()).all()
    return render_template('admin_reported_questions.html', reports=reports)

@admin_bp.route('/resolve_report/<int:report_id>', methods=['POST'])
@admin_required
def resolve_report(report_id):
    report = ReportedQuestion.query.get_or_404(report_id)
    report.is_resolved = True
    db.session.commit()
    flash('Report marked as resolved.', 'success')
    return redirect(url_for('admin.reported_questions'))

# --- API for Managing Categories ---
@admin_bp.route('/api/categories/<string:category_name>', methods=['GET', 'POST'])
@admin_required
def handle_categories(category_name):
    models = {'levels': Level, 'streams': Stream, 'boards': Board, 'subjects': Subject, 'chapters': Chapter, 'topics': Topic}
    model = models.get(category_name)
    if not model:
        return jsonify({'success': False, 'message': 'Invalid category'}), 404

    if request.method == 'GET':
        parent_map = {'streams': 'level_id', 'boards': 'stream_id', 'subjects': 'board_id', 'chapters': 'subject_id', 'topics': 'chapter_id'}
        parent_id_field = parent_map.get(category_name)
        parent_id = request.args.get('parent_id')
        query = model.query
        if parent_id and parent_id_field:
            query = query.filter(getattr(model, parent_id_field) == parent_id)
        items = query.all()
        if model == Board:
            return jsonify([{'id': item.id, 'name': item.name, 'tag': item.tag} for item in items])
        return jsonify([{'id': item.id, 'name': item.name} for item in items])
    
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'}), 400
        
        kwargs = {'name': name}
        if model == Board:
            kwargs['tag'] = data.get('tag')

        parent_map = {'streams': 'level_id', 'boards': 'stream_id', 'subjects': 'board_id', 'chapters': 'subject_id', 'topics': 'chapter_id'}
        if parent_map.get(category_name):
            parent_id = data.get('parent_id')
            if not parent_id:
                return jsonify({'success': False, 'message': 'Parent ID is required'}), 400
            kwargs[parent_map[category_name]] = parent_id
        
        try:
            new_item = model(**kwargs)
            db.session.add(new_item)
            db.session.commit()
            response_data = {'success': True, 'id': new_item.id, 'name': new_item.name}
            if model == Board:
                response_data['tag'] = new_item.tag
            return jsonify(response_data), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/api/categories/<string:category_name>/<int:item_id>', methods=['PUT', 'DELETE'])
@admin_required
def handle_category_item(category_name, item_id):
    models = {'levels': Level, 'streams': Stream, 'boards': Board, 'subjects': Subject, 'chapters': Chapter, 'topics': Topic}
    model = models.get(category_name)
    if not model:
        return jsonify({'success': False, 'message': 'Invalid category'}), 404

    item = model.query.get_or_404(item_id)
    
    if request.method == 'PUT':
        data = request.json
        try:
            item.name = data.get('name', item.name)
            if model == Board:
                item.tag = data.get('tag', item.tag)
            db.session.commit()
            response_data = {'success': True, 'id': item.id, 'name': item.name}
            if model == Board:
                response_data['tag'] = item.tag
            return jsonify(response_data)
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    if request.method == 'DELETE':
        if hasattr(item, 'streams') and item.streams.first():
            return jsonify({'success': False, 'message': 'Cannot delete. This item has child streams.'}), 400
        if hasattr(item, 'boards') and item.boards.first():
            return jsonify({'success': False, 'message': 'Cannot delete. This item has child boards.'}), 400
        if hasattr(item, 'subjects') and item.subjects.first():
            return jsonify({'success': False, 'message': 'Cannot delete. This item has child subjects.'}), 400
        if hasattr(item, 'chapters') and item.chapters.first():
            return jsonify({'success': False, 'message': 'Cannot delete. This item has child chapters.'}), 400
        if hasattr(item, 'topics') and item.topics.first():
            return jsonify({'success': False, 'message': 'Cannot delete. This item has child topics.'}), 400
        
        try:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
