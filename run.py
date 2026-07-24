"""TriviaVerse Application Entry Point"""
import os
from dotenv import load_dotenv
from app import create_app, socketio

load_dotenv()

config_name = os.environ.get('FLASK_ENV', 'development')

app = create_app(config_name)

if __name__ == '__main__':
    debug = config_name == 'development'
    socketio.run(app, debug=debug, allow_unsafe_werkzeug=debug)
