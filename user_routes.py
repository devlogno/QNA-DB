# user_routes.py
from flask import Blueprint, render_template, abort, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, DoubtPost, UserReport
from extensions import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/<string:public_id>')
@login_required
def public_profile(public_id):
    """Displays a user's public profile page."""
    user = User.query.filter_by(public_id=public_id).first_or_404()
    
    # Fetch recent doubt posts by this user
    recent_posts = DoubtPost.query.filter_by(user_id=user.id)\
                                  .order_by(DoubtPost.timestamp.desc())\
                                  .limit(10).all()

    return render_template('public_profile.html', user=user, posts=recent_posts)

@user_bp.route('/report/<string:public_id>', methods=['POST'])
@login_required
def report_user(public_id):
    """Handles reporting a user."""
    user_to_report = User.query.filter_by(public_id=public_id).first()
    if not user_to_report:
        return jsonify({'status': 'error', 'message': 'User not found.'}), 404
    
    if user_to_report.id == current_user.id:
        return jsonify({'status': 'error', 'message': 'You cannot report yourself.'}), 400

    reason = request.json.get('reason')
    if not reason:
        return jsonify({'status': 'error', 'message': 'A reason is required to report a user.'}), 400

    # Check if an unresolved report already exists
    existing_report = UserReport.query.filter_by(
        reporter_id=current_user.id,
        reported_id=user_to_report.id,
        is_resolved=False
    ).first()

    if existing_report:
        return jsonify({'status': 'info', 'message': 'You have already submitted a report for this user.'})

    new_report = UserReport(
        reporter_id=current_user.id,
        reported_id=user_to_report.id,
        reason=reason
    )
    db.session.add(new_report)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'User has been reported to the administrators. Thank you.'})
