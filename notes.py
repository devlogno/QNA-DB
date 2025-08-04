# notes.py
import os
import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Note, NoteImage, Level, Stream, Subject, Chapter, Topic, Board
from decorators import check_access

notes_bp = Blueprint('notes', __name__)

# --- Configurable limits defined directly in the file ---
FREE_USER_NOTE_LIMIT = 10
FREE_USER_STORAGE_LIMIT_BYTES = 10 * 1024 * 1024  # 10 MB
PREMIUM_USER_STORAGE_LIMIT_BYTES = 100 * 1024 * 1024 # 100 MB

def get_file_size(file):
    """Helper to get file size from a FileStorage object."""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0) # Reset file pointer
    return size

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

@notes_bp.route('/notes', methods=['GET', 'POST'])
@login_required
def view_notes():
    """Display all notes and handle creation of new notes."""
    is_premium = current_user.is_admin or (current_user.subscription_expiry and current_user.subscription_expiry > datetime.datetime.utcnow())

    if request.method == 'POST':
        if not is_premium and current_user.notes_left <= 0:
            flash('You have reached your limit for creating new notes. Please upgrade for unlimited notes.', 'warning')
            return redirect(url_for('payments.pricing_page'))

        content = request.form.get('content')
        image_files = request.files.getlist('images')

        max_storage = PREMIUM_USER_STORAGE_LIMIT_BYTES if is_premium else FREE_USER_STORAGE_LIMIT_BYTES
        new_files_size = sum(get_file_size(f) for f in image_files if f.filename)
        if current_user.note_storage_used_bytes + new_files_size > max_storage:
            flash(f'Uploading these images would exceed your storage limit of {max_storage / (1024*1024):.0f} MB.', 'danger')
            return redirect(url_for('notes.view_notes'))

        if not content:
            flash('Content is required!', 'danger')
        else:
            # Auto-generate title from the first 5 words of content
            title_words = content.split()
            title = ' '.join(title_words[:5])
            if len(title_words) > 5:
                title += '...'
            if not title:
                title = "Untitled Note"

            new_note = Note(
                title=title, content=content, author=current_user,
                level_id=request.form.get('level_id') or None,
                stream_id=request.form.get('stream_id') or None,
                board_id=request.form.get('board_id') or None,
                subject_id=request.form.get('subject_id') or None,
                chapter_id=request.form.get('chapter_id') or None,
                topic_id=request.form.get('topic_id') or None
            )
            db.session.add(new_note)
            
            if not is_premium:
                current_user.notes_left -= 1
            
            uploaded_size = 0
            for image_file in image_files:
                if image_file.filename != '':
                    file_size = get_file_size(image_file)
                    image_url = upload_file(image_file)
                    if image_url:
                        new_image = NoteImage(image_url=image_url, note=new_note, size_bytes=file_size)
                        db.session.add(new_image)
                        uploaded_size += file_size
            
            current_user.note_storage_used_bytes += uploaded_size
            
            db.session.commit()
            flash('Note added successfully!', 'success')
            return redirect(url_for('notes.view_notes'))

    # Logic for displaying the page (GET request)
    query = Note.query.filter_by(user_id=current_user.id)
    
    level_id = request.args.get('level_id', type=int)
    stream_id = request.args.get('stream_id', type=int)
    board_id = request.args.get('board_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    chapter_id = request.args.get('chapter_id', type=int)
    topic_id = request.args.get('topic_id', type=int)

    breadcrumb_items = []
    filter_options = {'title': 'Filter by Level', 'items': []}

    if topic_id:
        topic = db.session.get(Topic, topic_id)
        if topic:
            query = query.filter_by(topic_id=topic_id)
            breadcrumb_items.insert(0, {'name': topic.name, 'url': url_for('notes.view_notes', topic_id=topic.id)})
            breadcrumb_items.insert(0, {'name': topic.chapter.name, 'url': url_for('notes.view_notes', chapter_id=topic.chapter.id)})
            breadcrumb_items.insert(0, {'name': topic.chapter.subject.name, 'url': url_for('notes.view_notes', subject_id=topic.chapter.subject.id)})
            breadcrumb_items.insert(0, {'name': topic.chapter.subject.board.name, 'url': url_for('notes.view_notes', board_id=topic.chapter.subject.board.id)})
            breadcrumb_items.insert(0, {'name': topic.chapter.subject.board.stream.name, 'url': url_for('notes.view_notes', stream_id=topic.chapter.subject.board.stream.id)})
            breadcrumb_items.insert(0, {'name': topic.chapter.subject.board.stream.level.name, 'url': url_for('notes.view_notes', level_id=topic.chapter.subject.board.stream.level.id)})
            filter_options = {'title': 'No further categories', 'items': []}
    elif chapter_id:
        chapter = db.session.get(Chapter, chapter_id)
        if chapter:
            query = query.filter_by(chapter_id=chapter_id)
            breadcrumb_items.insert(0, {'name': chapter.name, 'url': url_for('notes.view_notes', chapter_id=chapter.id)})
            breadcrumb_items.insert(0, {'name': chapter.subject.name, 'url': url_for('notes.view_notes', subject_id=chapter.subject.id)})
            breadcrumb_items.insert(0, {'name': chapter.subject.board.name, 'url': url_for('notes.view_notes', board_id=chapter.subject.board.id)})
            breadcrumb_items.insert(0, {'name': chapter.subject.board.stream.name, 'url': url_for('notes.view_notes', stream_id=chapter.subject.board.stream.id)})
            breadcrumb_items.insert(0, {'name': chapter.subject.board.stream.level.name, 'url': url_for('notes.view_notes', level_id=chapter.subject.board.stream.level.id)})
            filter_options['title'] = 'Filter by Topic'
            filter_options['items'] = [{'name': t.name, 'url': url_for('notes.view_notes', topic_id=t.id)} for t in chapter.topics]
    elif subject_id:
        subject = db.session.get(Subject, subject_id)
        if subject:
            query = query.filter_by(subject_id=subject_id)
            breadcrumb_items.insert(0, {'name': subject.name, 'url': url_for('notes.view_notes', subject_id=subject.id)})
            breadcrumb_items.insert(0, {'name': subject.board.name, 'url': url_for('notes.view_notes', board_id=subject.board.id)})
            breadcrumb_items.insert(0, {'name': subject.board.stream.name, 'url': url_for('notes.view_notes', stream_id=subject.board.stream.id)})
            breadcrumb_items.insert(0, {'name': subject.board.stream.level.name, 'url': url_for('notes.view_notes', level_id=subject.board.stream.level.id)})
            filter_options['title'] = 'Filter by Chapter'
            filter_options['items'] = [{'name': c.name, 'url': url_for('notes.view_notes', chapter_id=c.id)} for c in subject.chapters]
    elif board_id:
        board = db.session.get(Board, board_id)
        if board:
            query = query.filter_by(board_id=board_id)
            breadcrumb_items.insert(0, {'name': board.name, 'url': url_for('notes.view_notes', board_id=board.id)})
            breadcrumb_items.insert(0, {'name': board.stream.name, 'url': url_for('notes.view_notes', stream_id=board.stream.id)})
            breadcrumb_items.insert(0, {'name': board.stream.level.name, 'url': url_for('notes.view_notes', level_id=board.stream.level.id)})
            filter_options['title'] = 'Filter by Subject'
            filter_options['items'] = [{'name': s.name, 'url': url_for('notes.view_notes', subject_id=s.id)} for s in board.subjects]
    elif stream_id:
        stream = db.session.get(Stream, stream_id)
        if stream:
            query = query.filter_by(stream_id=stream_id)
            breadcrumb_items.insert(0, {'name': stream.name, 'url': url_for('notes.view_notes', stream_id=stream.id)})
            breadcrumb_items.insert(0, {'name': stream.level.name, 'url': url_for('notes.view_notes', level_id=stream.level.id)})
            filter_options['title'] = 'Filter by Board'
            filter_options['items'] = [{'name': b.name, 'url': url_for('notes.view_notes', board_id=b.id)} for b in stream.boards]
    elif level_id:
        level = db.session.get(Level, level_id)
        if level:
            query = query.filter_by(level_id=level_id)
            breadcrumb_items.insert(0, {'name': level.name, 'url': url_for('notes.view_notes', level_id=level.id)})
            user_streams_in_level = sorted([s for s in current_user.streams if s.level_id == level_id], key=lambda x: x.name)
            filter_options['title'] = 'Filter by Stream'
            filter_options['items'] = [{'name': s.name, 'url': url_for('notes.view_notes', stream_id=s.id)} for s in user_streams_in_level]
    else:
        user_levels = sorted(list(set(s.level for s in current_user.streams)), key=lambda x: x.name)
        filter_options['items'] = [{'name': l.name, 'url': url_for('notes.view_notes', level_id=l.id)} for l in user_levels]

    notes = query.order_by(Note.timestamp.desc()).all()
    user_levels_data = [{'id': level.id, 'name': level.name} for level in sorted(list(set(s.level for s in current_user.streams)), key=lambda x: x.name)]
    
    max_storage_bytes = PREMIUM_USER_STORAGE_LIMIT_BYTES if is_premium else FREE_USER_STORAGE_LIMIT_BYTES

    return render_template('notes.html', 
                           notes=notes,
                           user_levels_data=user_levels_data,
                           breadcrumb_items=breadcrumb_items,
                           filter_options=filter_options,
                           notes_left=current_user.notes_left,
                           storage_used_mb=(current_user.note_storage_used_bytes / (1024*1024)),
                           max_storage_mb=(max_storage_bytes / (1024*1024))
                           )

@notes_bp.route('/notes/edit/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        flash('You are not authorized to edit this note.', 'danger')
        return redirect(url_for('notes.view_notes'))

    is_premium = current_user.is_admin or (current_user.subscription_expiry and current_user.subscription_expiry > datetime.datetime.utcnow())
    max_storage = PREMIUM_USER_STORAGE_LIMIT_BYTES if is_premium else FREE_USER_STORAGE_LIMIT_BYTES
    new_image_files = request.files.getlist('new_images')
    new_files_size = sum(get_file_size(f) for f in new_image_files if f.filename)

    if current_user.note_storage_used_bytes + new_files_size > max_storage:
        flash(f'Uploading these images would exceed your storage limit of {max_storage / (1024*1024):.0f} MB.', 'danger')
        return redirect(url_for('notes.view_notes'))

    content = request.form.get('content')
    
    if not content:
        flash('Content cannot be empty!', 'danger')
    else:
        # Auto-generate title from the first 5 words of content
        title_words = content.split()
        title = ' '.join(title_words[:5])
        if len(title_words) > 5:
            title += '...'
        if not title:
            title = "Untitled Note"

        note.title = title
        note.content = content
        note.level_id = request.form.get('level_id') or None
        note.stream_id = request.form.get('stream_id') or None
        note.board_id = request.form.get('board_id') or None
        note.subject_id = request.form.get('subject_id') or None
        note.chapter_id = request.form.get('chapter_id') or None
        note.topic_id = request.form.get('topic_id') or None
        
        uploaded_size = 0
        for image_file in new_image_files:
            if image_file.filename != '':
                file_size = get_file_size(image_file)
                image_url = upload_file(image_file)
                if image_url:
                    new_image = NoteImage(image_url=image_url, note_id=note.id, size_bytes=file_size)
                    db.session.add(new_image)
                    uploaded_size += file_size
        
        current_user.note_storage_used_bytes += uploaded_size
        db.session.commit()
        flash('Note updated successfully!', 'success')
    
    return redirect(url_for('notes.view_notes'))

@notes_bp.route('/notes/get_note_data/<int:note_id>')
@login_required
def get_note_data(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'level_id': note.level_id,
        'stream_id': note.stream_id,
        'board_id': note.board_id,
        'subject_id': note.subject_id,
        'chapter_id': note.chapter_id,
        'topic_id': note.topic_id
    })

@notes_bp.route('/notes/image/delete/<int:image_id>', methods=['DELETE'])
@login_required
def delete_note_image(image_id):
    image = NoteImage.query.get_or_404(image_id)
    note = image.note
    
    if note.author != current_user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        image_path = os.path.join(current_app.root_path, image.image_url.lstrip('/'))
        if os.path.exists(image_path):
            os.remove(image_path)

        current_user.note_storage_used_bytes -= image.size_bytes
        db.session.delete(image)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Image deleted.'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting image: {e}")
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500

@notes_bp.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        flash('You are not authorized to delete this note.', 'danger')
    else:
        storage_to_free = 0
        for image in note.images:
            storage_to_free += image.size_bytes
            try:
                image_path = os.path.join(current_app.root_path, image.image_url.lstrip('/'))
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error deleting file for note {note.id}: {e}")
        
        current_user.note_storage_used_bytes -= storage_to_free
        is_premium = current_user.subscription_expiry and current_user.subscription_expiry > datetime.datetime.utcnow()
        if not current_user.is_admin and not is_premium:
            current_user.notes_left += 1

        db.session.delete(note)
        db.session.commit()
        flash('Note deleted.', 'success')
        
    return redirect(url_for('notes.view_notes'))
