from flask import Blueprint, session, redirect, request, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db

lang_bp = Blueprint('lang', __name__)

@lang_bp.route('/set-language/<lang>')
def set_language(lang):
    """Хэл солих (сесс + хэрэглэгчийн профайл)"""
    if lang not in ('en', 'mn'):
        lang = 'en'

    session['language'] = lang

    if current_user.is_authenticated:
        current_user.language = lang
        db.session.commit()

    next_page = request.args.get('next') or request.referrer or url_for('home.index')
    return redirect(next_page)