# services/achievements_service.py
from extensions import db
from models import Badge, User, DoubtAnswer, ExamSession

def check_and_award_badge(user, badge_name):
    """
    Checks if a user has already earned a badge, and if not, awards it.
    Returns True if a new badge was awarded, False otherwise.
    """
    badge = Badge.query.filter_by(name=badge_name).first()
    if badge and badge not in user.badges:
        user.badges.append(badge)
        db.session.commit()
        return True
    return False

def check_all_achievements(user):
    """
    A central function to check all possible achievements for a user.
    Can be called after significant events (e.g., completing a quiz).
    """
    # --- Check for "First Answer" badge ---
    if DoubtAnswer.query.filter_by(user_id=user.id).count() >= 1:
        check_and_award_badge(user, "First Answer")

    # --- Check for "Question Solver" badges ---
    total_questions_solved = db.session.query(db.func.sum(ExamSession.total_questions)).filter_by(user_id=user.id).scalar() or 0
    if total_questions_solved >= 100:
        check_and_award_badge(user, "Century Solver")
    elif total_questions_solved >= 50:
        check_and_award_badge(user, "Half-Century Solver")
    elif total_questions_solved >= 10:
        check_and_award_badge(user, "Novice Solver")

    # Add more achievement checks here in the future (e.g., Subject Pro)

