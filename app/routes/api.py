from flask import Blueprint, current_app, jsonify, request, render_template
from flask_login import login_required, current_user
from app.extensions import db, utcnow
from app.models.user import User, DiscordAccount, Friend
from app.models.notification import Notification
from app.models.question import Question
from app.models.room import Room
from app.utils.notify import send_notification
from app.utils.search import search_questions, search_users, search_rooms

api_bp = Blueprint('api', __name__)

# ==========================================
#  Хэрэглэгчийн мэдээлэл (Discord ID-аар)
# ==========================================
@api_bp.route('/user/<discord_id>')
def get_user(discord_id):
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404

    user = discord_account.user
    return jsonify({
        'id': user.id,
        'username': user.username,
        'level': user.level,
        'xp': user.xp,
        'coins': user.coins,
        'wins': user.wins,
        'accuracy': user.accuracy,
        'games_played': user.games_played,
        'display_name': user.display_name,
        'avatar_url': user.avatar_url,
        'elo_rating': user.elo_rating,
        'reputation': user.reputation,
        'bank_balance': user.bank_balance,
        'spouse': User.query.get(user.spouse_id).username if user.spouse_id else None
    })

# ==========================================
#  Нэвтэрсэн хэрэглэгчийн статистик
# ==========================================
@api_bp.route('/user/stats')
@login_required
def api_user_stats():
    stats = {
        'username': current_user.username,
        'display_name': current_user.display_name,
        'level': current_user.level,
        'xp': current_user.xp,
        'coins': current_user.coins,
        'wins': current_user.wins,
        'losses': current_user.losses,
        'games_played': current_user.games_played,
        'accuracy': round(current_user.accuracy, 1),
        'avatar': current_user.avatar_url,
        'is_online': current_user.is_online
    }
    return jsonify(stats)

# ==========================================
#  Global Search (Chapter 16)
# ==========================================
@api_bp.route('/search')
@login_required
def global_search():
    """AJAX global search endpoint for questions, users, and rooms."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify({'results': []})

    results = {}

    if search_type in ('all', 'questions'):
        questions = search_questions(query, limit=limit)
        results['questions'] = [
            {
                'id': q.id,
                'text': q.question_text[:100],
                'category': q.category.name if q.category else None,
                'difficulty': q.difficulty
            }
            for q in questions
        ]

    if search_type in ('all', 'users'):
        users = search_users(query, limit=limit)
        results['users'] = [
            {
                'id': u.id,
                'username': u.username,
                'display_name': u.display_name,
                'avatar_url': u.avatar_url,
                'level': u.level
            }
            for u in users
        ]

    if search_type in ('all', 'rooms'):
        rooms = search_rooms(query, limit=limit)
        results['rooms'] = [
            {
                'id': r.id,
                'name': r.name,
                'code': r.code,
                'status': r.status,
                'player_count': r.max_players
            }
            for r in rooms
        ]

    return jsonify(results)


# ==========================================
#  Мэдэгдлүүд
# ==========================================
@api_bp.route('/notifications')
@login_required
def get_notifications():
    notifs = current_user.notifications.order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify([n.to_dict() for n in notifs])

@api_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    count = current_user.notifications.filter_by(is_read=False).count()
    return jsonify({'count': count})

@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

# ==========================================
#  Найзын систем (API)
# ==========================================
@api_bp.route('/friends/search', methods=['POST'])
def api_search_friends():
    data = request.json
    discord_id = data.get('discord_id')
    username = data.get('username')

    current_user_discord = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not current_user_discord or not current_user_discord.user:
        return jsonify({'error': 'Your account not found'}), 404

    sender = current_user_discord.user
    target = User.query.filter_by(username=username).first()
    if not target:
        return jsonify({'error': 'User not found'}), 404

    if target.id == sender.id:
        return jsonify({'error': 'Cannot add yourself'}), 400

    existing = Friend.query.filter(
        ((Friend.user_id == sender.id) & (Friend.friend_id == target.id)) |
        ((Friend.user_id == target.id) & (Friend.friend_id == sender.id))
    ).first()
    if existing:
        return jsonify({'error': 'Already friends or request pending'}), 409

    friendship = Friend(user_id=sender.id, friend_id=target.id, status='pending')
    db.session.add(friendship)
    db.session.commit()

    send_notification(
        user_id=target.id,
        title='New Friend Request',
        message=f'{sender.username} wants to be your friend!',
        notif_type='info'
    )

    return jsonify({'message': 'Friend request sent'})

@api_bp.route('/users/coins/add', methods=['POST'])
def add_coins():
    data = request.json
    discord_id = data.get('discord_id')
    amount = data.get('amount', 0)
    reason = data.get('reason', 'Discord activity')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    user.add_coins(amount, reason)
    db.session.commit()
    
    return jsonify({'new_coins': user.coins})

@api_bp.route('/users/xp/add', methods=['POST'])
def add_xp():
    data = request.json
    discord_id = data.get('discord_id')
    amount = data.get('amount', 0)
    reason = data.get('reason', 'Discord activity')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    level_up, old_lvl, new_lvl = user.add_xp(amount)
    db.session.commit()
    
    return jsonify({
        'xp': user.xp,
        'level': user.level,
        'level_up': level_up,
        'old_level': old_lvl,
        'new_level': new_lvl
    })

@api_bp.route('/discord/sync-role', methods=['POST'])
def discord_sync_role():
    data = request.get_json(silent=True) or {}
    discord_id = data.get('discord_id')
    level = data.get('level')
    if not discord_id or not isinstance(level, int) or level < 1:
        return jsonify({'error': 'discord_id and a positive level are required'}), 400
    try:
        import requests as req
        response = req.post(
            "http://localhost:9600/sync-role",
            json={"discord_id": discord_id, "level": level},
            timeout=(2, 5),
        )
        response.raise_for_status()
        return jsonify({'success': True})
    except req.RequestException:
        current_app.logger.exception('Discord role synchronization failed')
        return jsonify({'error': 'Failed'}), 500

# ==========================================
#  Economy & Banking
# ==========================================
@api_bp.route('/bank/deposit', methods=['POST'])
def bank_deposit():
    data = request.json
    discord_id = data.get('discord_id')
    amount = data.get('amount')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    if amount == 'all':
        amount = user.coins
    else:
        amount = int(amount)
        
    if amount <= 0 or user.coins < amount:
        return jsonify({'error': 'Invalid amount or insufficient coins'}), 400
        
    user.coins -= amount
    user.bank_balance += amount
    db.session.commit()
    return jsonify({'success': True, 'coins': user.coins, 'bank': user.bank_balance})

@api_bp.route('/bank/withdraw', methods=['POST'])
def bank_withdraw():
    data = request.json
    discord_id = data.get('discord_id')
    amount = data.get('amount')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    if amount == 'all':
        amount = user.bank_balance
    else:
        amount = int(amount)
        
    if amount <= 0 or user.bank_balance < amount:
        return jsonify({'error': 'Invalid amount or insufficient bank balance'}), 400
        
    user.bank_balance -= amount
    user.coins += amount
    db.session.commit()
    return jsonify({'success': True, 'coins': user.coins, 'bank': user.bank_balance})

@api_bp.route('/gamble/coinflip', methods=['POST'])
def gamble_coinflip():
    data = request.json
    discord_id = data.get('discord_id')
    bet = int(data.get('bet', 0))
    side = data.get('side', 'heads') # heads/tails
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    if bet <= 0 or user.coins < bet:
        return jsonify({'error': 'Invalid bet'}), 400
        
    import random
    result = random.choice(['heads', 'tails'])
    win = result == side
    
    if win:
        user.coins += bet
        msg = f"You won {bet} coins!"
    else:
        user.coins -= bet
        msg = f"You lost {bet} coins."
        
    db.session.commit()
    return jsonify({'success': True, 'win': win, 'result': result, 'message': msg, 'new_balance': user.coins})

@api_bp.route('/gamble/rob', methods=['POST'])
def gamble_rob():
    data = request.json
    discord_id = data.get('discord_id')
    target_id = data.get('target_id')
    
    sender_acc = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    target_acc = DiscordAccount.query.filter_by(discord_id=target_id).first()
    
    if not sender_acc or not target_acc:
        return jsonify({'error': 'User not found'}), 404
        
    sender = sender_acc.user
    target = target_acc.user
    
    if target.coins < 100:
        return jsonify({'error': 'Target is too poor to rob!'}), 400
        
    import random
    success = random.random() < 0.3 # 30% success
    
    if success:
        stolen = int(target.coins * random.uniform(0.1, 0.3))
        target.coins -= stolen
        sender.coins += stolen
        db.session.commit()
        return jsonify({'success': True, 'stolen': stolen, 'message': f"You successfully robbed {stolen} coins!"})
    else:
        fine = int(sender.coins * 0.1)
        sender.coins -= fine
        db.session.commit()
        return jsonify({'success': False, 'fine': fine, 'message': f"You got caught and fined {fine} coins!"})

@api_bp.route('/shop/items')
def api_shop_items():
    from app.models.shop import ShopItem
    items = ShopItem.query.filter_by(is_active=True).all()
    # Dynamic pricing: price = base_price * (1 + total_sold / 100)
    for item in items:
        item.price = int(item.base_price * (1 + item.total_sold / 100))
    return jsonify([item.to_dict() for item in items])

@api_bp.route('/buy', methods=['POST'])
def api_buy_item():
    from app.models.shop import ShopItem, UserInventory
    data = request.json
    discord_id = data.get('discord_id')
    item_id = data.get('item_id')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    item = ShopItem.query.get_or_404(item_id)
    
    current_price = int(item.base_price * (1 + item.total_sold / 100))
    if user.coins < current_price:
        return jsonify({'error': 'Insufficient coins'}), 402
        
    user.coins -= current_price
    item.total_sold += 1
    
    inv = UserInventory.query.filter_by(user_id=user.id, item_id=item.id).first()
    if inv:
        inv.quantity += 1
    else:
        inv = UserInventory(user_id=user.id, item_id=item.id, quantity=1)
        db.session.add(inv)
        
    db.session.commit()
    return jsonify({'success': True, 'item_name': item.name, 'coins_left': user.coins})

@api_bp.route('/daily', methods=['POST'])
def api_daily():
    from datetime import datetime, timedelta
    data = request.json
    discord_id = data.get('discord_id')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
        
    user = discord_account.user
    now = utcnow()
    
    if user.last_daily_reward and (now - user.last_daily_reward) < timedelta(hours=20):
        remaining = timedelta(hours=20) - (now - user.last_daily_reward)
        return jsonify({'success': False, 'message': f'Wait {int(remaining.total_seconds() // 3600)}h {int((remaining.total_seconds() % 3600) // 60)}m'}), 400
        
    reward = 100 * user.coin_multiplier
    user.coins += reward
    user.last_daily_reward = now
    db.session.commit()
    
    return jsonify({'success': True, 'reward': reward, 'new_coins': user.coins})

@api_bp.route('/user/rep/give', methods=['POST'])
def api_give_rep():
    from datetime import datetime, timedelta
    data = request.json
    discord_id = data.get('discord_id')
    target_id = data.get('target_id')
    
    sender_acc = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    target_acc = DiscordAccount.query.filter_by(discord_id=target_id).first()
    
    if not sender_acc or not target_acc:
        return jsonify({'error': 'User not found'}), 404
        
    sender = sender_acc.user
    target = target_acc.user
    now = utcnow()
    
    if sender.last_rep_given and (now - sender.last_rep_given) < timedelta(hours=24):
        return jsonify({'error': 'You can only give reputation once every 24 hours'}), 400
        
    target.reputation += 1
    sender.last_rep_given = now
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/user/marry', methods=['POST'])
def api_marry():
    data = request.json
    discord_id = data.get('discord_id')
    target_id = data.get('target_id')
    
    sender_acc = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    target_acc = DiscordAccount.query.filter_by(discord_id=target_id).first()
    
    if not sender_acc or not target_acc:
        return jsonify({'error': 'User not found'}), 404
        
    sender = sender_acc.user
    target = target_acc.user
    
    if sender.spouse_id or target.spouse_id:
        return jsonify({'error': 'One of the users is already married!'}), 400
        
    sender.spouse_id = target.id
    target.spouse_id = sender.id
    db.session.commit()
    return jsonify({'success': True})

# ==========================================
#  Bot Integration Endpoints
# ==========================================

@api_bp.route('/user/<discord_id>/inventory')
def api_user_inventory(discord_id):
    """Bot: Get user's inventory by Discord ID."""
    from app.models.shop import UserInventory
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    items = UserInventory.query.filter_by(user_id=user.id).all()
    return jsonify([item.to_dict() for item in items])

@api_bp.route('/equip', methods=['POST'])
def api_equip_item():
    """Bot: Equip an item from inventory."""
    from app.models.shop import UserInventory, ShopItem
    data = request.json
    discord_id = data.get('discord_id')
    item_id = data.get('item_id')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    inv = UserInventory.query.filter_by(user_id=user.id, item_id=item_id).first()
    if not inv:
        return jsonify({'error': 'Item not found in inventory'}), 404
    
    # Unequip all items of the same type
    item = ShopItem.query.get(item_id)
    if item and item.item_type:
        same_type_items = UserInventory.query.join(ShopItem).filter(
            UserInventory.user_id == user.id,
            ShopItem.item_type == item.item_type,
            UserInventory.is_equipped == True
        ).all()
        for i in same_type_items:
            i.is_equipped = False
    
    inv.is_equipped = True
    db.session.commit()
    return jsonify({'success': True, 'item_name': item.name if item else 'item'})

@api_bp.route('/notify', methods=['POST'])
def api_notify():
    """Bot: Send notification to user via Discord ID."""
    data = request.json
    discord_id = data.get('discord_id')
    title = data.get('title', 'Notification')
    message = data.get('message', '')
    notif_type = data.get('type', 'info')
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    send_notification(
        user_id=discord_account.user.id,
        title=title,
        message=message,
        notif_type=notif_type
    )
    return jsonify({'success': True})

@api_bp.route('/questions/random')
def api_random_question():
    """Bot: Get a random question for solo trivia."""
    from app.models.question import Answer, Category
    import random
    
    category_slug = request.args.get('category')
    query = Question.query.filter_by(is_active=True)
    
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    
    questions = query.all()
    if not questions:
        return jsonify({'error': 'No questions available'}), 404
    
    q = random.choice(questions)
    answers = Answer.query.filter_by(question_id=q.id).all()
    
    # Shuffle answers and track correct index
    answer_list = [(a.answer_text, a.is_correct) for a in answers]
    random.shuffle(answer_list)
    
    correct_index = next(i for i, (_, is_correct) in enumerate(answer_list) if is_correct)
    
    return jsonify({
        'id': q.id,
        'question': q.question_text,
        'question_text': q.question_text,
        'answers': [text for text, _ in answer_list],
        'answers_full': [{'answer_text': text, 'is_correct': is_correct} for text, is_correct in answer_list],
        'correct_index': correct_index,
        'category': q.category.name if q.category else 'General',
        'difficulty': q.difficulty
    })

@api_bp.route('/leaderboard')
def api_leaderboard():
    """Bot: Get leaderboard data."""
    from app.models.economy import LeaderboardEntry
    period = request.args.get('period', 'alltime')
    limit = min(int(request.args.get('limit', 10)), 25)
    
    if period not in ['daily', 'weekly', 'monthly', 'alltime']:
        period = 'alltime'
    
    entries = LeaderboardEntry.query.filter_by(period=period)\
        .order_by(LeaderboardEntry.score.desc()).limit(limit).all()
    
    data = []
    for entry in entries:
        user = User.query.get(entry.user_id)
        data.append({
            'username': user.username if user else 'Unknown',
            'score': entry.score,
            'wins': entry.wins,
            'games_played': entry.games_played,
            'accuracy': round(entry.accuracy, 1)
        })
    return jsonify(data)

@api_bp.route('/admin/server-stats')
def api_server_stats():
    """Bot: Get server statistics."""
    from app.models.question import Category
    total_users = User.query.count()
    total_questions = Question.query.count()
    total_categories = Category.query.count()
    active_rooms = Room.query.filter_by(status='waiting').count()
    
    return jsonify({
        'total_players': total_users,
        'total_questions': total_questions,
        'total_categories': total_categories,
        'active_rooms': active_rooms
    })

@api_bp.route('/boss/spawn', methods=['POST'])
def api_boss_spawn():
    """Bot: Spawn a boss."""
    from app.models.boss import Boss
    data = request.json
    name = data.get('name', 'World Boss')
    hp = data.get('hp', 100000)
    
    # Deactivate existing bosses
    Boss.query.filter_by(status='active').update({'status': 'defeated'})
    
    boss = Boss(name=name, max_hp=hp, current_hp=hp, status='active')
    db.session.add(boss)
    db.session.commit()
    
    return jsonify({
        'id': boss.id,
        'name': boss.name,
        'max_hp': boss.max_hp,
        'current_hp': boss.current_hp,
        'status': boss.status
    }), 201

@api_bp.route('/rooms/<code>')
def api_room_info(code):
    """Bot: Get room info by code."""
    room = Room.query.filter_by(code=code).first()
    if not room:
        return jsonify({'exists': False}), 404
    
    return jsonify({
        'exists': True,
        'name': room.name,
        'code': room.code,
        'status': room.status,
        'player_count': room.get_player_count(),
        'max_players': room.max_players,
        'game_mode': room.game_mode
    })

@api_bp.route('/boss/damage', methods=['POST'])
def api_boss_damage():
    """Bot: Apply damage to a boss."""
    from app.models.boss import Boss
    data = request.json
    boss_id = data.get('boss_id')
    discord_id = data.get('discord_id')
    damage = data.get('damage', 0)
    
    boss = Boss.query.get(boss_id)
    if not boss or boss.status != 'active':
        return jsonify({'error': 'Boss not found or not active'}), 404
    
    discord_account = DiscordAccount.query.filter_by(discord_id=discord_id).first()
    if not discord_account or not discord_account.user:
        return jsonify({'error': 'User not found'}), 404
    
    user = discord_account.user
    
    # Apply damage
    boss.current_hp = max(0, boss.current_hp - damage)
    
    # Reward XP and coins for damage
    xp_reward = max(1, damage // 100)
    coin_reward = max(1, damage // 200)
    user.add_xp(xp_reward)
    user.add_coins(coin_reward, f'Boss damage: {damage}')
    
    defeated = False
    if boss.current_hp <= 0:
        boss.status = 'defeated'
        boss.end_time = utcnow()
        defeated = True
        
        # Bonus rewards for defeating the boss
        user.add_coins(500, 'Boss defeat bonus')
        user.add_xp(200)
        
        send_notification(
            user_id=user.id,
            title='🐉 Boss Defeated!',
            message=f'You helped defeat {boss.name}! Bonus: 500 coins, 200 XP',
            notif_type='success'
        )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'defeated': defeated,
        'current_hp': boss.current_hp,
        'max_hp': boss.max_hp,
        'damage_dealt': damage,
        'xp_earned': xp_reward,
        'coins_earned': coin_reward
    })
