# Codebase Analysis Notes

## Bugs Found & Fixed
1. `config.py` - Mail config was outside Config class, causing import issues. FIXED.
2. `auth.py` - Referral code processed before `new_user` existed. FIXED.
3. `auth.py` - `forgot_password` had `pass` instead of sending email. FIXED.
4. `auth.py` - `reset_password` used `payload['user_id']` but token encodes `reset_password`. FIXED.
5. `quiz.py` - `submit_answer` used `question.correct_answer_id` which doesn't exist on model. FIXED to use `get_correct_answer()`.
6. `admin.py` - Missing imports for `Box`, `UserBox`, `requests`. FIXED.
7. `admin.py` - `user.boxes.delete()` used incorrect relationship. FIXED.
8. `api_bp.py` - Duplicate blueprint name `api_bp` conflicts with `api.py`. REMOVED (duplicate).
9. `email.py` - Broken `send_discord_error_log` reference, no password reset function. FIXED.
10. `extensions.py` - Missing `Babel` import. FIXED.

## Missing Features to Add
1. Full-text search (Chapter 16) - Elasticsearch stub
2. i18n/l10n (Chapter 13) - Flask-Babel setup
3. Docker deployment (Chapter 19)
4. Procfile for Heroku (Chapter 18)
5. Nginx config (Chapter 17)
6. AJAX search endpoint
7. Room search endpoint
8. User search endpoint
9. Fix room_socket.py start_game duplicate event name
10. Fix user_questions.py Room import missing

## Architecture Issues
1. `room_socket.py` and `game_socket.py` both define `start_game` event - duplicate
2. `api_bp.py` is a duplicate of parts of `api.py`
3. `user_questions.py` references `Room` without importing it
