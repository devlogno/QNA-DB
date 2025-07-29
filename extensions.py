# extensions.py
"""
This file initializes the Flask extensions to prevent circular imports.
The extensions are initialized in the application factory.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from flask_socketio import SocketIO

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
# --- ADDED: Initialize SocketIO ---
socketio = SocketIO()
