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


QUIZ_V2_TRANSLATIONS = {
    'mn': {
        'site_name': 'Trivia Quiz',
        'home_title': 'Оюуны тэмцээн',
        'home_subtitle': 'Мэдлэгээ сорь, дэлхийнхэнтэй өрсөлд!',
        'categories': 'Ангилалууд',
        'start_quiz': 'Тоглоом эхлүүлэх',
        'select_category': 'Ангилал сонгох',
        'difficulty': 'Хүндийн зэрэг',
        'easy': 'Хялбар',
        'medium': 'Дунд',
        'hard': 'Хүнд',
        'timer_on': 'Цагтай',
        'timer_off': 'Цаггүй',
        'question': 'Асуулт',
        'of': 'нээс',
        'score': 'Оноо',
        'streak': 'Дараалсан зөв',
        'best_score': 'Дээд оноо',
        'time_left': 'Үлдсэн цаг',
        'seconds': 'сек',
        'correct': 'Зөв!',
        'wrong': 'Буруу!',
        'quiz_complete': 'Дууслаа!',
        'your_score': 'Таны оноо',
        'correct_answers': 'Зөв хариулт',
        'wrong_answers': 'Буруу хариулт',
        'accuracy': 'Нарийвчлал',
        'play_again': 'Дахин тоглох',
        'back_home': 'Нүүр хуудас',
        'language': 'Хэл',
        'theme': 'Загвар',
        'dark': 'Бараан',
        'light': 'Гэрэлтэй',
        'loading': 'Ачаалж байна...',
        'error': 'Алдаа гарлаа',
        'retry': 'Дахин оролдох',
        'no_questions': 'Асуулт байхгүй',
        'select_difficulty': 'Хүндийн зэрэг сонгох',
        'number_of_questions': 'Асуултын тоо',
        'questions': 'Асуулт',
        'leaderboard': 'Тэргүүлэгчид',
        'settings': 'Тохиргоо',
    },
    'en': {
        'site_name': 'Trivia Quiz',
        'home_title': 'Trivia Quiz',
        'home_subtitle': 'Test your knowledge, compete with the world!',
        'categories': 'Categories',
        'start_quiz': 'Start Quiz',
        'select_category': 'Select Category',
        'difficulty': 'Difficulty',
        'easy': 'Easy',
        'medium': 'Medium',
        'hard': 'Hard',
        'timer_on': 'Timer On',
        'timer_off': 'Timer Off',
        'question': 'Question',
        'of': 'of',
        'score': 'Score',
        'streak': 'Streak',
        'best_score': 'Best Score',
        'time_left': 'Time Left',
        'seconds': 's',
        'correct': 'Correct!',
        'wrong': 'Wrong!',
        'quiz_complete': 'Quiz Complete!',
        'your_score': 'Your Score',
        'correct_answers': 'Correct',
        'wrong_answers': 'Wrong',
        'accuracy': 'Accuracy',
        'play_again': 'Play Again',
        'back_home': 'Back Home',
        'language': 'Language',
        'theme': 'Theme',
        'dark': 'Dark',
        'light': 'Light',
        'loading': 'Loading...',
        'error': 'Something went wrong',
        'retry': 'Retry',
        'no_questions': 'No questions available',
        'select_difficulty': 'Select Difficulty',
        'number_of_questions': 'Number of Questions',
        'questions': 'questions',
        'leaderboard': 'Leaderboard',
        'settings': 'Settings',
    }
}


def get_translations(lang='mn'):
    """Get translation dict for a specific language."""
    return QUIZ_V2_TRANSLATIONS.get(lang, QUIZ_V2_TRANSLATIONS['mn'])
