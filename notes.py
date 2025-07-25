# notes.py
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Note, NoteImage

notes_bp = Blueprint('notes', __name__)

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
    """Display all notes and handle creation of new notes with multiple images."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image_files = request.files.getlist('images') # Use getlist for multiple files

        if not title or not content:
            flash('Title and content are required!', 'danger')
        else:
            # Create the note first
            new_note = Note(
                title=title,
                content=content,
                author=current_user
            )
            db.session.add(new_note)
            
            # Process and add images
            for image_file in image_files:
                if image_file.filename != '':
                    image_url = upload_file(image_file)
                    if image_url:
                        new_image = NoteImage(image_url=image_url, note=new_note)
                        db.session.add(new_image)
            
            db.session.commit()
            flash('Note added successfully!', 'success')
            return redirect(url_for('notes.view_notes'))

    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.timestamp.desc()).all()
    return render_template('notes.html', notes=notes)

@notes_bp.route('/notes/edit/<int:note_id>', methods=['POST'])
@login_required
def edit_note(note_id):
    """Handle editing of an existing note's text content."""
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        flash('You are not authorized to edit this note.', 'danger')
        return redirect(url_for('notes.view_notes'))

    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        flash('Title and content cannot be empty!', 'danger')
    else:
        note.title = title
        note.content = content
        db.session.commit()
        flash('Note updated successfully!', 'success')
    
    return redirect(url_for('notes.view_notes'))

@notes_bp.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    """Handle deletion of a note and its associated images."""
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        flash('You are not authorized to delete this note.', 'danger')
    else:
        # The cascade delete in the model will handle deleting associated NoteImage objects
        db.session.delete(note)
        db.session.commit()
        flash('Note deleted.', 'success')
        
    return redirect(url_for('notes.view_notes'))
