# extensions.py
"""
This file initializes the Flask extensions to prevent circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()
