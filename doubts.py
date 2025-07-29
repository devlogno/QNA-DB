# doubts.py
import os
import base64
import uuid
from flask import Blueprint, render_template, request, jsonify, url_for, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from extensions import db, socketio
from models import DoubtPost, DoubtAnswer, PostImage, Notification
from flask_socketio import emit

doubts_bp = Blueprint('doubts', __name__)

def save_base64_image(image_b64):
    """Decodes a base64 string and saves it as an image file."""
    if not image_b64 or ',' not in image_b64:
        return None
    try:
        header, encoded = image_b64.split(',', 1)
        data = base64.b64decode(encoded)
        
        filename = f"{uuid.uuid4().hex}.png"
        upload_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], 'doubts')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(data)
            
        return url_for('static', filename=f'uploads/doubts/{filename}', _external=True)
    except Exception as e:
        print(f"Error saving base64 image: {e}")
        return None

@doubts_bp.route('/community')
@login_required
def community_forum():
    posts = DoubtPost.query.order_by(DoubtPost.timestamp.desc()).all()
    return render_template('doubts.html', posts=posts)

# --- SOCKET.IO EVENTS ---

@socketio.on('new_post')
def handle_new_post(data):
    if not current_user.is_authenticated: return
    
    title = data.get('title')
    content = data.get('content')
    image_b64 = data.get('image') # Expecting a single image string

    if not title or not content:
        emit('post_error', {'message': 'Title and content are required.'})
        return

    new_post = DoubtPost(user_id=current_user.id, title=title, content=content)
    db.session.add(new_post)
    db.session.flush()

    image_url = None
    if image_b64:
        image_url = save_base64_image(image_b64)
        if image_url:
            new_image = PostImage(image_url=image_url, post_id=new_post.id)
            db.session.add(new_image)
    
    db.session.commit()
    
    post_data = {
        'id': new_post.id,
        'title': new_post.title,
        'content': new_post.content,
        'author_name': new_post.author.name,
        'author_pic': new_post.author.profile_pic_url,
        'timestamp': new_post.timestamp.strftime('%b %d, %Y %I:%M %p'),
        'image': image_url, # Send single image URL
        'user_id': new_post.user_id,
        'is_admin': current_user.is_admin
    }
    emit('post_created', post_data, broadcast=True)

@socketio.on('new_answer')
def handle_new_answer(data):
    if not current_user.is_authenticated: return

    post_id = data.get('post_id')
    parent_id = data.get('parent_id')
    content = data.get('content')
    image_b64 = data.get('image')

    if not content:
        emit('answer_error', {'message': 'Answer content cannot be empty.'})
        return

    post = db.session.get(DoubtPost, post_id)
    if not post:
        emit('answer_error', {'message': 'Original post not found.'})
        return

    # --- MODIFIED: Thread Limiting Logic ---
    # If replying to a reply, attach to the original answer instead.
    if parent_id:
        parent_answer = db.session.get(DoubtAnswer, parent_id)
        if parent_answer and parent_answer.parent_id:
            parent_id = parent_answer.parent_id # Re-assign to the top-level answer
    
    new_answer = DoubtAnswer(user_id=current_user.id, post_id=post_id, parent_id=parent_id, content=content)
    db.session.add(new_answer)
    db.session.flush()

    image_url = None
    if image_b64:
        image_url = save_base64_image(image_b64)
        if image_url:
            new_image = PostImage(image_url=image_url, answer_id=new_answer.id)
            db.session.add(new_image)
    
    db.session.commit()

    # --- Notification Logic ---
    notify_user_id = None
    original_poster = None
    if parent_id:
        parent_answer = db.session.get(DoubtAnswer, parent_id)
        if parent_answer and parent_answer.user_id != current_user.id:
            notify_user_id = parent_answer.user_id
            original_poster = parent_answer.author
    elif post.user_id != current_user.id:
        notify_user_id = post.user_id
        original_poster = post.author

    if notify_user_id:
        notification_message = f"{current_user.name} replied to your post: '{post.title[:30]}...'"
        notification_link = url_for('doubts.community_forum', _anchor=f'answer-{new_answer.id}')
        new_notification = Notification(user_id=notify_user_id, message=notification_message, link_url=notification_link)
        db.session.add(new_notification)
        db.session.commit()
        socketio.emit('new_notification', {'message': notification_message, 'link': notification_link}, room=f'user_{notify_user_id}')
    
    answer_data = {
        'id': new_answer.id,
        'post_id': new_answer.post_id,
        'parent_id': new_answer.parent_id,
        'content': new_answer.content,
        'author_name': new_answer.author.name,
        'author_pic': new_answer.author.profile_pic_url,
        'timestamp': new_answer.timestamp.strftime('%b %d, %Y %I:%M %p'),
        'image': image_url,
        'user_id': new_answer.user_id,
        'is_admin': current_user.is_admin
    }
    emit('answer_created', answer_data, broadcast=True)

@socketio.on('delete_post')
def handle_delete_post(data):
    if not current_user.is_authenticated: return
    post_id = data.get('post_id')
    post = db.session.get(DoubtPost, post_id)
    if post and (post.user_id == current_user.id or current_user.is_admin):
        db.session.delete(post)
        db.session.commit()
        emit('post_deleted', {'post_id': post_id}, broadcast=True)

@socketio.on('delete_answer')
def handle_delete_answer(data):
    if not current_user.is_authenticated: return
    answer_id = data.get('answer_id')
    answer = db.session.get(DoubtAnswer, answer_id)
    if answer and (answer.user_id == current_user.id or current_user.is_admin):
        db.session.delete(answer)
        db.session.commit()
        emit('answer_deleted', {'answer_id': answer_id}, broadcast=True)

@socketio.on('join')
def on_join(data):
    if current_user.is_authenticated:
        from flask_socketio import join_room
        room = f"user_{current_user.id}"
        join_room(room)
