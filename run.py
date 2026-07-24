import os
from app import create_app, socketio

config_name = os.getenv('FLASK_ENV', 'development')  # 'development' эсвэл 'production'
app = create_app(config_name)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, use_reloader=False)