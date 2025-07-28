# gemini_ai.py
import os
import google.generativeai as genai
from flask import (
    Blueprint, render_template, request, jsonify, current_app, url_for
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import ChatHistory
from PIL import Image

gemini_bp = Blueprint('gemini', __name__)

# Configure the Gemini API client
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
except Exception as e:
    print(f"Error configuring Gemini API: {e}")

def upload_file(file):
    """Saves an uploaded file and returns its path relative to the static folder."""
    if file and file.filename != '':
        try:
            filename = secure_filename(file.filename)
            # Create a user-specific directory
            user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'doubts', str(current_user.id))
            os.makedirs(user_upload_dir, exist_ok=True)
            
            filepath = os.path.join(user_upload_dir, filename)
            file.save(filepath)
            
            # Return a path with forward slashes, relative to the 'static' folder
            relative_path = os.path.join('uploads', 'doubts', str(current_user.id), filename)
            return relative_path.replace("\\", "/")
        except Exception as e:
            print(f"Error uploading file for doubt solver: {e}")
            return None
    return None

@gemini_bp.route('/doubt-solver')
@login_required
def doubt_solver_page():
    """Renders the main doubt solver page with chat history."""
    chat_history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).all()
    return render_template('doubt_solver.html', chat_history=chat_history)

@gemini_bp.route('/doubt-solver/ask', methods=['POST'])
@login_required
def ask_gemini():
    """Handles the API request to the Gemini model."""
    if 'prompt' not in request.form:
        return jsonify({'error': 'No prompt provided.'}), 400

    prompt_text = request.form['prompt']
    image_file = request.files.get('image')
    
    image_path_for_db = None
    model_input = [prompt_text]

    try:
        if image_file:
            image_path_for_db = upload_file(image_file)
            image_file.seek(0)
            img = Image.open(image_file)
            model_input.append(img)

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(model_input)
        ai_response = response.text

        new_chat = ChatHistory(
            user_id=current_user.id,
            prompt=prompt_text,
            image_url=image_path_for_db,
            response=ai_response
        )
        db.session.add(new_chat)
        db.session.commit()

        return jsonify({
            'response': ai_response,
            'prompt': prompt_text,
            'image_url': url_for('static', filename=image_path_for_db) if image_path_for_db else None,
            'chat_id': new_chat.id,
            'timestamp': new_chat.timestamp.strftime('%b %d, %Y %I:%M %p')
        })

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({'error': f'An error occurred. Details: {str(e)}'}), 500

@gemini_bp.route('/doubt-solver/delete/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Deletes a specific chat history record for the current user."""
    chat_to_delete = ChatHistory.query.get_or_404(chat_id)

    if chat_to_delete.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        if chat_to_delete.image_url:
            # The image_url is stored relative to the static folder
            file_path = os.path.join(current_app.static_folder, chat_to_delete.image_url)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(chat_to_delete)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Chat deleted successfully.'})

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting chat: {e}")
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500
