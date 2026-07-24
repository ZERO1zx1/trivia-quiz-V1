"""Internationalization Utilities (Chapter 13)"""
from flask import request, session
from flask_babel import get_locale


def get_locale():
    """Get user's preferred locale."""
    # Check session first
    if 'locale' in session:
        return session['locale']
    # Check Accept-Language header
    return request.accept_languages.best_match(['en', 'mn']) or 'en'


def set_locale(lang):
    """Set user's preferred locale in session."""
    session['locale'] = lang


def get_translations():
    """Get available translations."""
    return {
        'en': 'English',
        'mn': 'Монгол',
        'ko': '한국어',
        'ja': '日本語',
        'zh': '中文',
    }
