"""Guild System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models.guild import Guild, GuildMember, GuildRank, GuildQuest, GuildWar, GuildBoss
from app.models.user import User
from app.utils.admin import admin_required

guild_bp = Blueprint('guild', __name__, url_prefix='/guild')


@guild_bp.route('/')
def index():
    """Guild list page"""
    page = request.args.get('page', 1, type=int)
    region = request.args.get('region', 'global')
    search = request.args.get('search', '')

    query = Guild.query.filter_by(is_active=True)
    if region != 'global':
        query = query.filter_by(region=region)
    if search:
        query = query.filter(Guild.name.ilike(f'%{search}%'))

    guilds = query.order_by(Guild.level.desc(), Guild.member_count.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    if current_user.is_authenticated:
        my_guild = GuildMember.query.filter_by(user_id=current_user.id).first()
    else:
        my_guild = None

    return render_template('guild/index.html', guilds=guilds, my_guild=my_guild)


@guild_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new guild"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        tag = request.form.get('tag', '').strip().upper()

        if not name or len(name) < 3 or len(name) > 50:
            flash('Guild name must be between 3 and 50 characters.', 'danger')
            return redirect(url_for('guild.create'))

        if not tag or len(tag) < 2 or len(tag) > 10:
            flash('Guild tag must be between 2 and 10 characters.', 'danger')
            return redirect(url_for('guild.create'))

        if Guild.query.filter_by(name=name).first():
            flash('Guild name already exists.', 'danger')
            return redirect(url_for('guild.create'))

        if Guild.query.filter_by(tag=tag).first():
            flash('Guild tag already exists.', 'danger')
            return redirect(url_for('guild.create'))

        guild = Guild(
            name=name,
            tag=tag,
            description=request.form.get('description', ''),
            owner_id=current_user.id,
            level=1,
            xp=0,
            coins=1000
        )
        db.session.add(guild)
        db.session.flush()

        # Create default ranks
        ranks = [
            ('Owner', '#FFD700', 100),
            ('Co-Leader', '#FF4500', 80),
            ('Leader', '#4169E1', 60),
            ('Officer', '#32CD32', 40),
            ('Member', '#87CEEB', 20),
            ('Recruit', '#999999', 10)
        ]
        for rank_name, color, order in ranks:
            rank = GuildRank(guild_id=guild.id, name=rank_name, color=color, order=order)
            db.session.add(rank)

        db.session.flush()

        # Make creator the owner
        owner_rank = GuildRank.query.filter_by(guild_id=guild.id, name='Owner').first()
        member = GuildMember(
            guild_id=guild.id,
            user_id=current_user.id,
            rank_id=owner_rank.id,
            coins_contributed=1000
        )
        db.session.add(member)
        db.session.commit()

        flash(f'Guild "{name}" created successfully!', 'success')
        return redirect(url_for('guild.detail', guild_id=guild.id))

    return render_template('guild/create.html')


@guild_bp.route('/<int:guild_id>')
def detail(guild_id):
    """Guild detail page"""
    guild = Guild.query.get_or_404(guild_id)
    members = GuildMember.query.filter_by(guild_id=guild.id).order_by(
        db.func.coalesce(GuildRank.order, 0).desc()
    ).join(GuildRank, GuildMember.rank_id == GuildRank.id).all()
    quests = GuildQuest.query.filter_by(guild_id=guild.id, is_completed=False).limit(10).all()

    my_membership = None
    if current_user.is_authenticated:
        my_membership = GuildMember.query.filter_by(
            guild_id=guild.id, user_id=current_user.id
        ).first()

    return render_template('guild/detail.html', guild=guild, members=members,
                           quests=quests, my_membership=my_membership)


@guild_bp.route('/<int:guild_id>/join', methods=['POST'])
@login_required
def join(guild_id):
    """Join a guild"""
    guild = Guild.query.get_or_404(guild_id)

    if GuildMember.query.filter_by(user_id=current_user.id).first():
        flash('You are already in a guild.', 'warning')
        return redirect(url_for('guild.detail', guild_id=guild_id))

    if guild.member_count >= guild.max_members:
        flash('Guild is full.', 'danger')
        return redirect(url_for('guild.detail', guild_id=guild_id))

    recruit_rank = GuildRank.query.filter_by(guild_id=guild.id, name='Recruit').first()
    member = GuildMember(
        guild_id=guild.id,
        user_id=current_user.id,
        rank_id=recruit_rank.id
    )
    guild.member_count += 1
    guild.last_activity = db.func.now()
    db.session.add(member)
    db.session.commit()

    flash(f'You joined {guild.name}!', 'success')
    return redirect(url_for('guild.detail', guild_id=guild_id))


@guild_bp.route('/<int:guild_id>/leave', methods=['POST'])
@login_required
def leave(guild_id):
    """Leave a guild"""
    member = GuildMember.query.filter_by(
        guild_id=guild_id, user_id=current_user.id
    ).first_or_404()

    guild = Guild.query.get(guild_id)

    # Cannot leave if owner
    if member.rank and member.rank.name == 'Owner':
        # Transfer ownership or disband
        other_members = GuildMember.query.filter(
            GuildMember.guild_id == guild_id,
            GuildMember.id != member.id
        ).first()
        if other_members:
            flash('You must transfer ownership before leaving.', 'warning')
            return redirect(url_for('guild.detail', guild_id=guild_id))
        else:
            db.session.delete(guild)
            db.session.commit()
            flash('Guild disbanded.', 'info')
            return redirect(url_for('guild.index'))

    db.session.delete(member)
    guild.member_count = max(0, guild.member_count - 1)
    db.session.commit()

    flash('You left the guild.', 'info')
    return redirect(url_for('guild.index'))


@guild_bp.route('/<int:guild_id>/quest', methods=['POST'])
@login_required
def complete_quest(guild_id):
    """Complete a guild quest"""
    quest_id = request.form.get('quest_id', type=int)
    quest = GuildQuest.query.get_or_404(quest_id)

    if quest.guild_id != guild_id:
        return jsonify({'error': 'Invalid quest'}), 400

    quest.is_completed = True
    quest.guild.xp += quest.reward_xp
    quest.guild.coins += quest.reward_coins

    # Update member contribution
    member = GuildMember.query.filter_by(guild_id=guild_id, user_id=current_user.id).first()
    if member:
        member.xp_contributed += quest.reward_xp

    db.session.commit()

    return jsonify({'success': True, 'xp': quest.reward_xp, 'coins': quest.reward_coins})


@guild_bp.route('/<int:guild_id>/invite', methods=['POST'])
@login_required
def invite(guild_id):
    """Invite a user to the guild"""
    username = request.form.get('username', '').strip()
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('guild.detail', guild_id=guild_id))

    if GuildMember.query.filter_by(user_id=user.id).first():
        flash('User is already in a guild.', 'warning')
        return redirect(url_for('guild.detail', guild_id=guild_id))

    # In production, send notification to user
    flash(f'Invitation sent to {username}.', 'success')
    return redirect(url_for('guild.detail', guild_id=guild_id))


# API endpoints
@guild_bp.route('/api/list')
def api_list():
    """API: List guilds"""
    page = request.args.get('page', 1, type=int)
    region = request.args.get('region', 'global')
    query = Guild.query.filter_by(is_active=True)
    if region != 'global':
        query = query.filter_by(region=region)

    guilds = query.order_by(Guild.level.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        'guilds': [g.to_dict() for g in guilds.items],
        'total': guilds.total,
        'pages': guilds.pages,
        'current_page': guilds.page
    })


@guild_bp.route('/api/<int:guild_id>')
def api_detail(guild_id):
    """API: Guild detail"""
    guild = Guild.query.get_or_404(guild_id)
    data = guild.to_dict()
    data['members'] = [m.to_dict() for m in guild.members.limit(50).all()]
    return jsonify(data)
