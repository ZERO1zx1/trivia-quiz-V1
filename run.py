"""TriviaVerse Application Runner"""
import os
from app import create_app, socketio

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
