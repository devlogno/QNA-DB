# user_profile.py
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Level, Stream, User, SavedQuestion, ReportedQuestion, ExamSession
from sqlalchemy import func

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if current_user.streams:
        flash('Your account is already set up.', 'info')
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        selected_stream_ids = request.form.getlist('streams', type=int)
        if not selected_stream_ids:
            flash('You must select at least one stream to continue.', 'danger')
            return redirect(url_for('profile.setup'))
        
        selected_streams = Stream.query.filter(Stream.id.in_(selected_stream_ids)).all()
        current_user.streams = selected_streams
        db.session.commit()
        
        flash('Your study preferences have been saved!', 'success')
        return redirect(url_for('routes.dashboard'))

    all_levels = Level.query.order_by(Level.name).all()
    return render_template('setup.html', all_levels=all_levels)


@profile_bp.route('/', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_school = request.form.get('school')
        
        if not new_name:
            flash('Name cannot be empty.', 'danger')
        else:
            current_user.name = new_name
            current_user.school = new_school
            flash('Personal information updated successfully!', 'success')

        if 'profile_pic' in request.files and request.files['profile_pic'].filename != '':
            file = request.files['profile_pic']
            try:
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                current_user.profile_pic_url = url_for('static', filename=f'uploads/{filename}')
                flash('Profile picture updated successfully!', 'success')
            except Exception as e:
                flash(f'Error uploading file: {e}', 'danger')
        
        selected_stream_ids = request.form.getlist('streams', type=int)
        if not selected_stream_ids:
            flash('You must select at least one stream.', 'warning')
        else:
            selected_streams = Stream.query.filter(Stream.id.in_(selected_stream_ids)).all()
            current_user.streams = selected_streams
            flash('Study streams updated successfully!', 'success')

        db.session.commit()
        return redirect(url_for('profile.profile'))

    # --- ADDED: Calculate total study time ---
    total_seconds = db.session.query(func.sum(ExamSession.time_taken_seconds)).filter_by(user_id=current_user.id).scalar() or 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    study_time_str = f"{hours}h {minutes}m"

    all_levels = Level.query.order_by(Level.name).all()
    user_stream_ids = {stream.id for stream in current_user.streams}
    return render_template('profile.html', all_levels=all_levels, user_stream_ids=user_stream_ids, study_time=study_time_str)

@profile_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password')
    if not current_user.check_password(password):
        flash('Incorrect password. Account deletion failed.', 'danger')
        return redirect(url_for('profile.profile'))
    try:
        user_to_delete = User.query.get(current_user.id)
        user_to_delete.streams.clear()
        # You might want to delete other user-related data here
        db.session.delete(user_to_delete)
        db.session.commit()
        logout_user()
        flash('Your account has been successfully deleted.', 'success')
        return redirect(url_for('routes.home'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during account deletion: {e}', 'danger')
        return redirect(url_for('profile.profile'))
