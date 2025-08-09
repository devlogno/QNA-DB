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


#Note subjects for a specific level and stream
@api_bp.route('/api/subjects/level/<int:level_id>/stream/<int:stream_id>')
def get_subjects_for_level_and_stream(level_id, stream_id):
    """
    Fetches unique subjects by name based on a given level and stream.
    This bypasses the need to select a board first.
    """
    # Query all subjects matching the level and stream
    subjects_query = Subject.query.filter_by(level_id=level_id, stream_id=stream_id).all()
    
    # Use a dictionary to filter for unique subject names in Python
    # This avoids potential issues with database-specific 'distinct' behavior
    # and ensures a clean list is returned to the user.
    unique_subjects = {}
    for s in subjects_query:
        if s.name not in unique_subjects:
            unique_subjects[s.name] = {'id': s.id, 'name': s.name}
    
    # Return the unique subjects as a JSON list
    return jsonify(list(unique_subjects.values()))