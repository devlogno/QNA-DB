# api.py
from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import Level, Stream, Board, Subject, Chapter, Topic

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/categories/<string:category_name>')
@login_required
def get_categories(category_name):
    """
    Provides category data to any authenticated user, primarily for populating
    cascading dropdowns in the notes section.
    """
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
        return jsonify({'success': False, 'message': 'Invalid category'}), 404

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
    
    # Boards have an extra 'tag' field we might want in the future,
    # but for now, a consistent name/id format is best.
    return jsonify([{'id': item.id, 'name': item.name} for item in items])