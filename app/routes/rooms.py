"""Room Routes"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import random
import string

from app.extensions import db
from app.models.room import Room, RoomPlayer
from app.models.question import Category
from app.utils.notify import send_notification

rooms_bp = Blueprint('rooms', __name__)

def generate_room_code():
    """6 тэмдэгттэй, давхардалгүй код үүсгэх"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Room.query.filter_by(code=code).first():
            return code

@rooms_bp.route('/')
@login_required
def lobby():
    page = request.args.get('page', 1, type=int)
    query = Room.query.filter_by(status='waiting')
    if request.args.get('private') == 'false':
        query = query.filter_by(is_private=False)
    rooms = query.order_by(db.desc('created_at')).paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('rooms/lobby.html', rooms=rooms, categories=categories)

@rooms_bp.route('/create', methods=['POST'])
@login_required
def create_room():
    name = request.form.get('name', 'Trivia Room').strip()
    is_private = 'is_private' in request.form
    password = request.form.get('password', '').strip() or None
    category_id = request.form.get('category_id', type=int)
    difficulty = request.form.get('difficulty', 'mixed')
    question_count = request.form.get('question_count', 10, type=int)
    max_players = request.form.get('max_players', 8, type=int)

    if not name:
        flash('Room name is required.', 'danger')
        return redirect(url_for('rooms.lobby'))

    # Хязгаарлалт шалгах
    question_count = min(max(question_count, 5), 50)
    max_players = min(max(max_players, 2), 8)

    room = Room(
        code=generate_room_code(),
        name=name,
        host_id=current_user.id,
        is_private=is_private,
        password=password,
        category_id=category_id if category_id else None,
        difficulty=difficulty,
        question_count=question_count,
        max_players=max_players
    )

    db.session.add(room)
    db.session.flush()  # room.id авахын тулд

    # Үүсгэгчийг автоматаар өрөөнд оруулах
    room_player = RoomPlayer(room_id=room.id, user_id=current_user.id, is_ready=True)
    db.session.add(room_player)
    db.session.commit()

    flash(f'Room created! Code: {room.code}', 'success')
    return redirect(url_for('rooms.room', code=room.code))

@rooms_bp.route('/join', methods=['POST'])
@login_required
def join_room():
    code = request.form.get('code', '').strip().upper()
    password = request.form.get('password', '').strip()

    room = Room.query.filter_by(code=code).first()
    if not room:
        flash('Room not found.', 'danger')
        return redirect(url_for('rooms.lobby'))
    if room.status != 'waiting':
        flash('This room is no longer accepting players.', 'danger')
        return redirect(url_for('rooms.lobby'))
    if room.is_full():
        flash('Room is full.', 'danger')
        return redirect(url_for('rooms.lobby'))
    if room.is_private and room.password != password:
        flash('Incorrect password.', 'danger')
        return redirect(url_for('rooms.lobby'))

    existing = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
    if existing:
        return redirect(url_for('rooms.room', code=code))

    room_player = RoomPlayer(room_id=room.id, user_id=current_user.id)
    db.session.add(room_player)
    db.session.commit()

    # Хэрэв өрөө дүүрсэн бол эзэнд мэдэгдэх (хүсвэл)
    if room.is_full():
        host = room.host
        if host and host.id != current_user.id:
            send_notification(
                user_id=host.id,
                title='Room Full',
                message=f'Your room {room.name} is now full!',
                notif_type='info'
            )

    return redirect(url_for('rooms.room', code=code))

@rooms_bp.route('/<code>')
@login_required
def room(code):
    room = Room.query.filter_by(code=code).first_or_404()
    player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()

    if not player and room.status == 'waiting':
        if room.is_full():
            flash('Room is full.', 'danger')
            return redirect(url_for('rooms.lobby'))
        if not room.is_private:
            player = RoomPlayer(room_id=room.id, user_id=current_user.id)
            db.session.add(player)
            db.session.commit()
        else:
            flash('This room requires a password.', 'warning')
            return redirect(url_for('rooms.lobby'))

    players = RoomPlayer.query.filter_by(room_id=room.id).all()
    is_host = room.host_id == current_user.id
    return render_template('rooms/room.html', room=room, players=players, is_host=is_host, current_player=player)

@rooms_bp.route('/<code>/leave', methods=['POST'])
@login_required
def leave_room(code):
    room = Room.query.filter_by(code=code).first_or_404()
    player = RoomPlayer.query.filter_by(room_id=room.id, user_id=current_user.id).first()
    if player:
        db.session.delete(player)
        if room.host_id == current_user.id:
            next_player = RoomPlayer.query.filter(
                RoomPlayer.room_id == room.id,
                RoomPlayer.user_id != current_user.id
            ).first()
            if next_player:
                room.host_id = next_player.user_id
                # Шинэ хостод мэдэгдэх
                send_notification(
                    user_id=next_player.user_id,
                    title='You are now the host',
                    message=f'You are now the host of room {room.name}.',
                    notif_type='info'
                )
            else:
                db.session.delete(room)
        db.session.commit()
    return redirect(url_for('rooms.lobby'))

@rooms_bp.route('/<code>/kick/<int:user_id>', methods=['POST'])
@login_required
def kick_player(code, user_id):
    room = Room.query.filter_by(code=code).first_or_404()
    if room.host_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot kick yourself'}), 400
    player = RoomPlayer.query.filter_by(room_id=room.id, user_id=user_id).first()
    if player:
        db.session.delete(player)
        db.session.commit()
        # Хөөгдсөн тоглогчид мэдэгдэл
        send_notification(
            user_id=user_id,
            title='Kicked from room',
            message=f'You have been kicked from room {room.name}.',
            notif_type='warning'
        )
        return jsonify({'success': True})
    return jsonify({'error': 'Player not found'}), 404