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
    rooms = query.order_by(db.desc(Room.created_at)).paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('rooms/lobby.html', rooms=rooms, categories=categories)

@rooms_bp.route('/create', methods=['POST'])
def create_room():
    """Create a room. Supports both web (login_required) and bot (discord_id) access."""
    if request.is_json:
        data = request.json
        name = data.get('name', 'Trivia Room').strip()
        is_private = data.get('private', False)
        password = data.get('password')
        category_id = data.get('category_id')
        difficulty = data.get('difficulty', 'mixed')
        question_count = data.get('question_count', 10)
        max_players = data.get('max_players', 8)
        game_mode = data.get('game_mode', 'classic')
        time_attack_duration = data.get('time_attack_duration', 15)
        survival_lives = data.get('survival_lives', 3)
        host_discord_id = data.get('host_discord_id')
        opponent_discord_id = data.get('opponent_discord_id')
        bet = data.get('bet', 0)
        
        if host_discord_id:
            from app.models.user import DiscordAccount
            da = DiscordAccount.query.filter_by(discord_id=host_discord_id).first()
            if da:
                host_user = da.user
            else:
                return jsonify({'error': 'Host not found'}), 404
        elif current_user.is_authenticated:
            host_user = current_user
        else:
            return jsonify({'error': 'Authentication required'}), 401
    else:
        if not current_user.is_authenticated:
            flash('Please log in to create a room.', 'warning')
            return redirect(url_for('auth.login'))
        name = request.form.get('name', 'Trivia Room').strip()
        is_private = 'is_private' in request.form
        password = request.form.get('password', '').strip() or None
        category_id = request.form.get('category_id', type=int)
        difficulty = request.form.get('difficulty', 'mixed')
        question_count = request.form.get('question_count', 10, type=int)
        max_players = request.form.get('max_players', 8, type=int)
        game_mode = request.form.get('game_mode', 'classic')
        time_attack_duration = request.form.get('time_attack_duration', 15, type=int)
        survival_lives = request.form.get('survival_lives', 3, type=int)
        opponent_discord_id = None
        bet = 0
        host_user = current_user

    if not name:
        if request.is_json:
            return jsonify({'error': 'Room name is required'}), 400
        flash('Room name is required.', 'danger')
        return redirect(url_for('rooms.lobby'))

    question_count = min(max(question_count, 5), 50)
    max_players = min(max(max_players, 2), 8)

    room = Room(
        code=generate_room_code(),
        name=name,
        host_id=host_user.id,
        is_private=is_private,
        password=password,
        category_id=category_id if category_id else None,
        difficulty=difficulty,
        question_count=question_count,
        max_players=max_players,
        game_mode=game_mode,
        time_attack_duration=time_attack_duration,
        survival_lives=survival_lives
    )

    db.session.add(room)
    db.session.flush()

    room_player = RoomPlayer(room_id=room.id, user_id=host_user.id, is_ready=True)
    db.session.add(room_player)
    
    # For duel mode: add opponent if specified
    if opponent_discord_id:
        from app.models.user import DiscordAccount
        opponent_da = DiscordAccount.query.filter_by(discord_id=opponent_discord_id).first()
        if opponent_da and opponent_da.user:
            opponent_player = RoomPlayer(room_id=room.id, user_id=opponent_da.user.id, is_ready=False)
            db.session.add(opponent_player)
            # Notify opponent about the duel
            send_notification(
                user_id=opponent_da.user.id,
                title='⚔️ Quiz Duel Challenge!',
                message=f'{host_user.username} challenged you to a quiz duel for {bet} coins! Room: {room.code}',
                notif_type='game_invite'
            )
    
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'code': room.code}), 201

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