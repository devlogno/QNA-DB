import os
import sys

# Add the project directory to the system's path
# This ensures that your application modules can be found
sys.path.insert(0, os.path.dirname(__file__))

# Import the create_app function from your app.py file
from app import create_app

# Import the socketio instance
from extensions import socketio

# Call the factory function to create the Flask application instance
# This is the key change to make the app factory pattern work.
application = create_app()

# We no longer use socketio.run() in a production environment.
# Instead, the WSGI server (like Passenger) runs the application,
# and SocketIO is handled as middleware. We do this by simply
# having the app object available. The 'socketio' instance is already
# linked to the 'app' instance via 'socketio.init_app(app)' in your create_app() function.
# The Passenger server will find the 'application' variable and serve it.
# If you were to use Gunicorn with eventlet, the command would be:
# gunicorn --worker-class eventlet -w 1 app:application
