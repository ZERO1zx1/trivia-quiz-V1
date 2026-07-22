"""Home Routes"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.models.question import Category
from app.models.room import Room
from app.models.economy import LeaderboardEntry
from app.models.user import User

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    # ★ Хэрэв нэвтэрсэн бол Dashboard руу чиглүүлэх
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # Нэвтрээгүй хэрэглэгчдэд зориулсан лендинг
    categories = Category.query.filter_by(is_active=True).all()
    public_rooms = Room.query.filter_by(is_private=False, status='waiting').limit(10).all()
    top_players = LeaderboardEntry.query.filter_by(period='alltime')\
        .order_by(LeaderboardEntry.score.desc()).limit(5).all()
    total_players = User.query.count()
    return render_template('home/index.html',
                         categories=categories,
                         public_rooms=public_rooms,
                         top_players=top_players,
                         total_players=total_players)