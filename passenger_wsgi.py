import os
import sys

# Add the project directory to the system's path
# This ensures that your application modules can be found
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app instance from your main app file
# The 'from app import app as application' assumes your Flask app instance
# is named 'app' inside your 'app.py' file.
try:
    from app import app as application
except ImportError:
    # If your app instance is created within a function, you might need to call it.
    # For example, if you have a create_app() function in app.py:
    # from app import create_app
    # application = create_app()
    pass