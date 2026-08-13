"""Production Gunicorn configuration for Flask-SocketIO on Render."""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'eventlet')
workers = 1
threads = 1
timeout = 120
graceful_timeout = 30
keepalive = 5
accesslog = '-'
errorlog = '-'
capture_output = True
