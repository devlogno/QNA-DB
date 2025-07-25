# notifications.py
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import db, Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications/mark-as-read', methods=['POST'])
@login_required
def mark_as_read():
    """Marks all unread notifications for the current user as read."""
    try:
        # Mark user-specific notifications as read
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        
        # Mark broadcast notifications as read for the current user.
        # This is a simplified approach. A more robust system would track read status per user for broadcasts.
        # For now, we assume opening the panel means "reading" all visible broadcasts.
        # A truly robust implementation would need a many-to-many table (User, Notification, is_read)
        Notification.query.filter_by(user_id=None, is_read=False).update({'is_read': True})

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Notifications marked as read.'})
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notifications as read: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred.'}), 500
