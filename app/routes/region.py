"""Region System Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.region import Region, RegionLeaderboard
from app.models.user import User

region_bp = Blueprint('region', __name__, url_prefix='/region')


@region_bp.route('/')
def index():
    """Region overview page"""
    regions = Region.query.filter_by(is_active=True).all()
    return render_template('region/index.html', regions=regions)


@region_bp.route('/<region_code>')
def detail(region_code):
    """Region detail page with leaderboard"""
    region = Region.query.filter_by(code=region_code).first_or_404()
    page = request.args.get('page', 1, type=int)

    leaderboard = RegionLeaderboard.query.filter_by(
        region_id=region.id
    ).order_by(RegionLeaderboard.rank).paginate(
        page=page, per_page=50, error_out=False
    )

    # Get user's rank in this region
    my_rank = None
    if current_user.is_authenticated:
        my_rank = RegionLeaderboard.query.filter_by(
            region_id=region.id, user_id=current_user.id
        ).first()

    return render_template('region/detail.html', region=region,
                           leaderboard=leaderboard, my_rank=my_rank)


@region_bp.route('/change', methods=['POST'])
@login_required
def change_region():
    """Change user's region"""
    new_region = request.form.get('region', '').strip().lower()
    region = Region.query.filter_by(code=new_region).first()

    if not region or not region.is_active:
        flash('Invalid region.', 'danger')
        return redirect(url_for('dashboard.index'))

    current_user.country = region.name
    db.session.commit()

    flash(f'Region changed to {region.name}!', 'success')
    return redirect(url_for('dashboard.index'))


# API endpoints
@region_bp.route('/api/list')
def api_list():
    """API: List all regions"""
    regions = Region.query.filter_by(is_active=True).all()
    return jsonify({
        'regions': [r.to_dict() for r in regions]
    })


@region_bp.route('/api/<region_code>/leaderboard')
def api_leaderboard(region_code):
    """API: Region leaderboard"""
    region = Region.query.filter_by(code=region_code).first_or_404()
    page = request.args.get('page', 1, type=int)

    entries = RegionLeaderboard.query.filter_by(
        region_id=region.id
    ).order_by(RegionLeaderboard.rank).paginate(
        page=page, per_page=50, error_out=False
    )

    return jsonify({
        'region': region.to_dict(),
        'leaderboard': [
            {
                'rank': e.rank,
                'user': e.user.to_dict() if e.user else None,
                'xp': e.xp,
                'wins': e.wins,
                'accuracy': e.accuracy,
                'level': e.level,
                'elo_rating': e.elo_rating
            }
            for e in entries.items
        ],
        'total': entries.total,
        'pages': entries.pages
    })


@region_bp.route('/api/update/<int:user_id>', methods=['POST'])
@login_required
def api_update_rank(user_id):
    """API: Update user's region rank (called after game)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin only'}), 403

    user = User.query.get_or_404(user_id)
    region_code = request.json.get('region', user.country).lower()
    region = Region.query.filter_by(code=region_code).first()

    if not region:
        return jsonify({'error': 'Region not found'}), 404

    entry = RegionLeaderboard.query.filter_by(
        region_id=region.id, user_id=user.id
    ).first()

    if entry:
        entry.xp = user.xp
        entry.wins = user.wins
        entry.accuracy = user.accuracy
        entry.level = user.level
        entry.elo_rating = user.elo_rating
        entry.last_updated = db.func.now()
    else:
        entry = RegionLeaderboard(
            region_id=region.id,
            user_id=user.id,
            xp=user.xp,
            wins=user.wins,
            accuracy=user.accuracy,
            level=user.level,
            elo_rating=user.elo_rating
        )
        db.session.add(entry)

    # Recalculate ranks
    entries = RegionLeaderboard.query.filter_by(region_id=region.id).order_by(
        RegionLeaderboard.xp.desc()
    ).all()

    for i, e in enumerate(entries, 1):
        e.rank = i

    region.player_count = entries
    db.session.commit()

    return jsonify({'success': True})
