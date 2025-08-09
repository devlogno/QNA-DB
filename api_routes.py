# api_routes.py
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import (
    Level, Stream, Board, Subject, Chapter, Topic, Question, 
    NewsArticle, Note, ExamSession, User, Notification
)
from extensions import db
from sqlalchemy import func, or_
import datetime

api_routes_bp = Blueprint('api_routes', __name__, url_prefix='/api')

# Auth endpoints
@api_routes_bp.route('/auth/me')
@login_required
def get_current_user():
    return jsonify({
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'school': current_user.school,
            'profile_pic_url': current_user.profile_pic_url,
            'is_admin': current_user.is_admin,
            'points': current_user.points,
            'subscription_expiry': current_user.subscription_expiry.isoformat() if current_user.subscription_expiry else None,
            'mcq_views_left': current_user.mcq_views_left,
            'cq_views_left': current_user.cq_views_left,
            'exams_left': current_user.exams_left,
            'ai_doubts_left': current_user.ai_doubts_left,
            'notes_left': current_user.notes_left,
        }
    })

# Dashboard stats
@api_routes_bp.route('/dashboard/stats')
@login_required
def get_dashboard_stats():
    user_stream_ids = [stream.id for stream in current_user.streams]
    
    question_query = Question.query
    if user_stream_ids:
        question_query = question_query.filter(Question.stream_id.in_(user_stream_ids))

    total_questions = question_query.count()
    total_mcqs = question_query.filter(Question.question_type == 'MCQ').count()
    total_cqs = question_query.filter(Question.question_type == 'CQ').count()

    total_seconds = db.session.query(func.sum(ExamSession.time_taken_seconds)).filter_by(user_id=current_user.id).scalar() or 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    study_time_str = f"{hours}h {minutes}m"

    return jsonify({
        'total_questions': total_questions,
        'total_mcqs': total_mcqs,
        'total_cqs': total_cqs,
        'study_time': study_time_str
    })

# Categories endpoints
@api_routes_bp.route('/categories/<string:category_name>')
@login_required
def get_categories(category_name):
    models = {
        'levels': Level, 
        'streams': Stream, 
        'boards': Board, 
        'subjects': Subject, 
        'chapters': Chapter, 
        'topics': Topic
    }
    model = models.get(category_name)

    if not model:
        return jsonify({'error': 'Invalid category'}), 404

    parent_map = {
        'streams': 'level_id', 
        'boards': 'stream_id', 
        'subjects': 'board_id', 
        'chapters': 'subject_id', 
        'topics': 'chapter_id'
    }
    parent_id_field = parent_map.get(category_name)
    parent_id = request.args.get('parent_id')
    
    query = model.query
    if parent_id and parent_id_field:
        query = query.filter(getattr(model, parent_id_field) == parent_id)
    
    items = query.order_by(model.name).all()
    
    result = []
    for item in items:
        item_data = {'id': item.id, 'name': item.name}
        if hasattr(item, 'tag') and item.tag:
            item_data['tag'] = item.tag
        result.append(item_data)
    
    return jsonify(result)

# Questions endpoints
@api_routes_bp.route('/questions')
@login_required
def get_questions():
    board_id = request.args.get('board_id', type=int)
    question_type = request.args.get('question_type', '').upper()
    page = request.args.get('page', 1, type=int)
    per_page = 50

    if not board_id or question_type not in ['MCQ', 'CQ']:
        return jsonify({'error': 'Invalid parameters'}), 400

    questions_pagination = Question.query.filter(
        Question.board_id == board_id,
        Question.question_type == question_type
    ).order_by(Question.year.desc(), Question.id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    saved_question_ids = {sq.question_id for sq in current_user.saved_questions}
    
    questions_data = []
    for q in questions_pagination.items:
        question_data = {
            'id': q.id,
            'question_text': q.question_text,
            'question_image_url': q.question_image_url,
            'question_type': q.question_type,
            'year': q.year,
            'complexity': q.complexity,
            'is_saved': q.id in saved_question_ids,
            'board': {'name': q.board.name, 'tag': q.board.tag} if q.board else None,
            'subject': {'name': q.subject.name} if q.subject else None,
        }
        
        if q.question_type == 'MCQ':
            question_data.update({
                'option_a': q.option_a,
                'option_b': q.option_b,
                'option_c': q.option_c,
                'option_d': q.option_d,
                'option_a_image_url': q.option_a_image_url,
                'option_b_image_url': q.option_b_image_url,
                'option_c_image_url': q.option_c_image_url,
                'option_d_image_url': q.option_d_image_url,
                'correct_answer': q.correct_answer,
                'solution': q.solution,
                'solution_image_url': q.solution_image_url,
            })
        else:  # CQ
            question_data.update({
                'question_a': q.question_a,
                'question_b': q.question_b,
                'question_c': q.question_c,
                'question_d': q.question_d,
                'answer_a': q.answer_a,
                'answer_b': q.answer_b,
                'answer_c': q.answer_c,
                'answer_d': q.answer_d,
            })
        
        questions_data.append(question_data)

    return jsonify({
        'questions': questions_data,
        'pagination': {
            'page': questions_pagination.page,
            'pages': questions_pagination.pages,
            'per_page': questions_pagination.per_page,
            'total': questions_pagination.total,
            'has_next': questions_pagination.has_next,
            'has_prev': questions_pagination.has_prev,
        }
    })

# News endpoints
@api_routes_bp.route('/news')
@login_required
def get_news():
    user_level_ids = {stream.level_id for stream in current_user.streams}
    user_stream_ids = {stream.id for stream in current_user.streams}

    filters = []
    filters.append(db.and_(NewsArticle.level_id.is_(None), NewsArticle.stream_id.is_(None)))
    
    if user_level_ids:
        filters.append(db.and_(NewsArticle.level_id.in_(user_level_ids), NewsArticle.stream_id.is_(None)))
        
    if user_stream_ids:
        filters.append(NewsArticle.stream_id.in_(user_stream_ids))

    articles = NewsArticle.query.filter(or_(*filters)).order_by(NewsArticle.timestamp.desc()).all()
    user_votes = {vote.article_id: vote.vote_type for vote in current_user.news_votes}
    
    articles_data = []
    for article in articles:
        article_data = {
            'id': article.id,
            'title': article.title,
            'content': article.content,
            'image_url': article.image_url,
            'timestamp': article.timestamp.isoformat(),
            'upvotes': article.upvotes,
            'downvotes': article.downvotes,
            'user_vote': user_votes.get(article.id, 0),
            'level': {'name': article.level.name} if article.level else None,
            'stream': {'name': article.stream.name} if article.stream else None,
        }
        articles_data.append(article_data)
    
    return jsonify({'articles': articles_data})

# Notifications endpoints
@api_routes_bp.route('/notifications')
@login_required
def get_notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    broadcast_notifications = Notification.query.filter_by(user_id=None).order_by(Notification.timestamp.desc()).all()
    all_notifications = sorted(user_notifications + broadcast_notifications, key=lambda x: x.timestamp, reverse=True)
    
    unread_user_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    # Calculate unread broadcast notifications (simplified for API)
    unread_broadcast_count = 0  # This would need more complex logic
    
    notifications_data = []
    for notification in all_notifications:
        notifications_data.append({
            'id': notification.id,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat(),
            'is_read': notification.is_read,
            'link_url': notification.link_url,
        })
    
    return jsonify({
        'notifications': notifications_data,
        'unread_count': unread_user_count + unread_broadcast_count
    })

@api_routes_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500