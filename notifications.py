# notifications.py
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Notification, BroadcastNotificationView

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications/mark-as-read', methods=['POST'])
@login_required
def mark_as_read():
    """
    Marks all unread notifications for the current user as read.
    - For user-specific notifications, it sets the 'is_read' flag to True.
    - For broadcast notifications, it creates a record in the BroadcastNotificationView
      table to track that the current user has seen them.
    """
    try:
        # 1. Mark all of the user's direct notifications as read
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})

        # 2. Get the IDs of all broadcast notifications the user has already seen
        read_broadcast_ids = {view.notification_id for view in current_user.read_broadcast_notifications}

        # 3. Find all broadcast notifications that are new to this user
        all_broadcast_notifications = Notification.query.filter(Notification.user_id.is_(None)).all()
        
        unread_broadcasts = [
            n for n in all_broadcast_notifications if n.id not in read_broadcast_ids
        ]

        # 4. Create "view" records for these newly seen broadcast notifications
        for notification in unread_broadcasts:
            view = BroadcastNotificationView(
                user_id=current_user.id,
                notification_id=notification.id
            )
            db.session.add(view)

        # 5. Commit all changes to the database
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Notifications marked as read.'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notifications as read: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred.'}), 500
