# decorators.py
from functools import wraps
from flask import flash, redirect, url_for, request, jsonify
from flask_login import current_user
from extensions import db
import datetime

def check_access(feature=None):
    """
    A decorator that checks if a user is logged in and has access to a feature.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login'))

            if current_user.is_admin or (current_user.subscription_expiry and current_user.subscription_expiry > datetime.datetime.utcnow()):
                return f(*args, **kwargs)

            if not feature:
                return f(*args, **kwargs)

            usage_map = {
                'mcq_answer': 'mcq_views_left',
                'cq_answer': 'cq_views_left',
                'exams': 'exams_left',
                'ai_doubts': 'ai_doubts_left',
                'notes': 'notes_left' # --- ADDED: Note feature ---
            }
            
            counter_attr = usage_map.get(feature)
            if not counter_attr:
                return f(*args, **kwargs)

            uses_left = getattr(current_user, counter_attr, 0)

            if uses_left > 0:
                # For notes, we don't decrement here. It's done in the route after success.
                if feature != 'notes':
                    setattr(current_user, counter_attr, uses_left - 1)
                    db.session.commit()
                return f(*args, **kwargs)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'status': 'limit_reached', 
                        'message': 'You have reached your usage limit for this feature.',
                        'redirect_url': url_for('payments.pricing_page')
                    }), 403
                else:
                    flash('You have reached your usage limit. Please upgrade for unlimited access.', 'warning')
                    return redirect(url_for('payments.pricing_page'))

        return decorated_function
    return decorator
