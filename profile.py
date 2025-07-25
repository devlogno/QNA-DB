# profile.py
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename
from models import db, ReportedQuestion, SavedQuestion, Level, User # Import Level and User

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # --- Handle Profile Picture ---
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
        
        # --- Handle Level Updates ---
        selected_level_ids = request.form.getlist('levels', type=int)
        if not selected_level_ids:
            flash('You must select at least one level.', 'warning')
        else:
            selected_levels = Level.query.filter(Level.id.in_(selected_level_ids)).all()
            current_user.levels = selected_levels
            flash('Study levels updated successfully!', 'success')

        db.session.commit()
        return redirect(url_for('profile.profile'))

    # For GET request, fetch all levels and the user's selected level IDs
    all_levels = Level.query.order_by(Level.name).all()
    user_level_ids = {level.id for level in current_user.levels}
    return render_template('profile.html', all_levels=all_levels, user_level_ids=user_level_ids)

@profile_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Handles user account deletion."""
    password = request.form.get('password')

    if not current_user.check_password(password):
        flash('Incorrect password. Account deletion failed.', 'danger')
        return redirect(url_for('profile.profile'))

    try:
        user_to_delete = User.query.get(current_user.id)

        # The cascade deletes in the User model should handle associations,
        # but explicit deletion can be safer for many-to-many if cascades aren't set.
        # Here, we clear the levels relationship.
        user_to_delete.levels.clear()

        # Explicitly delete other related items if cascade is not trusted
        SavedQuestion.query.filter_by(user_id=user_to_delete.id).delete()
        ReportedQuestion.query.filter_by(reporter_id=user_to_delete.id).delete()
        
        db.session.delete(user_to_delete)
        db.session.commit()
        logout_user()
        flash('Your account has been successfully deleted.', 'success')
        return redirect(url_for('routes.home'))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during account deletion: {e}', 'danger')
        return redirect(url_for('profile.profile'))
