"""Battle Pass Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db, utcnow
from app.models.battle_pass import Season, BattlePass, BattlePassReward, BattlePassProgress
from datetime import datetime

battle_pass_bp = Blueprint('battle_pass', __name__, url_prefix='/battle-pass')


@battle_pass_bp.route('/')
def index():
    """Battle Pass main page"""
    active_season = Season.query.filter_by(is_active=True).first()

    if not active_season:
        return render_template('battle_pass/index.html', active_season=None, progress=None)

    free_pass = BattlePass.query.filter_by(season_id=active_season.id, tier='free').first()
    premium_pass = BattlePass.query.filter_by(season_id=active_season.id, tier='premium').first()

    progress = None
    if current_user.is_authenticated and free_pass:
        progress = BattlePassProgress.query.filter_by(
            user_id=current_user.id, battle_pass_id=free_pass.id
        ).first()

    return render_template('battle_pass/index.html',
                           active_season=active_season,
                           free_pass=free_pass,
                           premium_pass=premium_pass,
                           progress=progress)


@battle_pass_bp.route('/<int:pass_id>/claim/<int:level>', methods=['POST'])
@login_required
def claim_reward(pass_id, level):
    """Claim a battle pass reward"""
    pass_item = BattlePass.query.get_or_404(pass_id)
    reward = BattlePassReward.query.filter_by(
        battle_pass_id=pass_id, level=level, tier=pass_item.tier
    ).first()

    if not reward:
        return jsonify({'error': 'Reward not found'}), 404

    progress = BattlePassProgress.query.filter_by(
        user_id=current_user.id, battle_pass_id=pass_id
    ).first()

    if not progress:
        return jsonify({'error': 'No progress found'}), 404

    if progress.current_level < level:
        return jsonify({'error': 'Level not reached yet'}), 400

    # Check if already claimed
    claimed = []
    if progress.claimed_levels:
        import json
        claimed = json.loads(progress.claimed_levels)

    if level in claimed:
        return jsonify({'error': 'Already claimed'}), 400

    # Check premium requirement
    if pass_item.tier == 'premium' and not progress.is_premium:
        return jsonify({'error': 'Premium required'}), 403

    # Grant reward
    _grant_reward(current_user, reward)

    # Mark as claimed
    claimed.append(level)
    progress.claimed_levels = json.dumps(claimed)
    progress.last_claimed_at = utcnow()
    db.session.commit()

    return jsonify({'success': True, 'reward': reward.reward_name})


@battle_pass_bp.route('/premium/upgrade', methods=['POST'])
@login_required
def upgrade_premium():
    """Upgrade to premium battle pass"""
    active_season = Season.query.filter_by(is_active=True).first()
    if not active_season:
        flash('No active season.', 'warning')
        return redirect(url_for('battle_pass.index'))

    free_pass = BattlePass.query.filter_by(season_id=active_season.id, tier='free').first()
    premium_pass = BattlePass.query.filter_by(season_id=active_season.id, tier='premium').first()

    if not free_pass or not premium_pass:
        flash('Battle pass not available.', 'warning')
        return redirect(url_for('battle_pass.index'))

    # Check if already premium
    progress = BattlePassProgress.query.filter_by(
        user_id=current_user.id, battle_pass_id=free_pass.id
    ).first()

    if progress and progress.is_premium:
        flash('Already premium.', 'info')
        return redirect(url_for('battle_pass.index'))

    # Create premium progress or upgrade existing
    premium_progress = BattlePassProgress.query.filter_by(
        user_id=current_user.id, battle_pass_id=premium_pass.id
    ).first()

    if not premium_progress:
        premium_progress = BattlePassProgress(
            user_id=current_user.id,
            battle_pass_id=premium_pass.id,
            current_level=progress.current_level if progress else 0,
            xp=progress.xp if progress else 0,
            is_premium=True
        )
        db.session.add(premium_progress)

    if progress:
        progress.is_premium = True

    db.session.commit()

    flash('Upgraded to Premium Battle Pass!', 'success')
    return redirect(url_for('battle_pass.index'))


@battle_pass_bp.route('/api/season/<int:season_id>/rewards')
def api_season_rewards(season_id):
    """API: Get season rewards"""
    passes = BattlePass.query.filter_by(season_id=season_id).all()
    data = {}
    for p in passes:
        rewards = BattlePassReward.query.filter_by(
            battle_pass_id=p.id
        ).order_by(BattlePassReward.level).all()
        data[p.tier] = [
            {
                'level': r.level,
                'reward_type': r.reward_type,
                'reward_name': r.reward_name,
                'rarity': r.rarity
            }
            for r in rewards
        ]
    return jsonify(data)


@battle_pass_bp.route('/api/progress')
@login_required
def api_progress():
    """API: Get battle pass progress"""
    active_season = Season.query.filter_by(is_active=True).first()
    if not active_season:
        return jsonify({'error': 'No active season'}), 404

    free_pass = BattlePass.query.filter_by(season_id=active_season.id, tier='free').first()
    if not free_pass:
        return jsonify({'error': 'No battle pass'}), 404

    progress = BattlePassProgress.query.filter_by(
        user_id=current_user.id, battle_pass_id=free_pass.id
    ).first()

    if not progress:
        # Create initial progress
        progress = BattlePassProgress(
            user_id=current_user.id,
            battle_pass_id=free_pass.id,
            current_level=0,
            xp=0,
            xp_needed=100
        )
        db.session.add(progress)
        db.session.commit()

    return jsonify(progress.to_dict())


def _grant_reward(user, reward):
    """Grant a battle pass reward to user"""
    if reward.reward_type == 'coins':
        user.coins += reward.reward_value
    elif reward.reward_type == 'xp':
        user.add_xp(reward.reward_value)
    # Other types would be handled by adding to inventory
    user.update_accuracy()
