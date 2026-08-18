"""Community / Forum Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db, utcnow
from app.models.community import ForumCategory, ForumPost, ForumComment, ForumLike, UserBookmark
from datetime import datetime

community_bp = Blueprint('community', __name__, url_prefix='/community')


@community_bp.route('/')
def index():
    """Forum main page"""
    categories = ForumCategory.query.filter_by(is_active=True).order_by(ForumCategory.order).all()
    recent_posts = ForumPost.query.order_by(ForumPost.created_at.desc()).limit(10).all()

    return render_template('community/forum.html', categories=categories, recent_posts=recent_posts)


@community_bp.route('/category/<int:category_id>')
def category(category_id):
    """View forum category"""
    category = ForumCategory.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'newest')

    query = ForumPost.query.filter_by(category_id=category.id, is_pinned=False)
    if sort_by == 'popular':
        query = query.order_by(ForumPost.like_count.desc())
    elif sort_by == 'discussed':
        query = query.order_by(ForumPost.comment_count.desc())
    else:
        query = query.order_by(ForumPost.created_at.desc())

    posts = query.paginate(page=page, per_page=20, error_out=False)
    pinned_posts = ForumPost.query.filter_by(
        category_id=category.id, is_pinned=True
    ).order_by(ForumPost.created_at.desc()).all()

    return render_template('community/category.html', category=category,
                           posts=posts, pinned_posts=pinned_posts, sort_by=sort_by)


@community_bp.route('/post/<int:post_id>')
def view_post(post_id):
    """View a forum post"""
    post = ForumPost.query.get_or_404(post_id)
    post.view_count += 1
    db.session.commit()

    comments = post.comments.filter_by(is_deleted=False).order_by(
        ForumComment.created_at
    ).all()

    liked = False
    bookmarked = False
    if current_user.is_authenticated:
        liked = ForumLike.query.filter_by(post_id=post.id, user_id=current_user.id).first() is not None
        bookmarked = UserBookmark.query.filter_by(user_id=current_user.id, post_id=post.id).first() is not None

    return render_template('community/post.html', post=post, comments=comments,
                           liked=liked, bookmarked=bookmarked)


@community_bp.route('/post/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a forum post"""
    if request.method == 'POST':
        post = ForumPost(
            category_id=request.form.get('category_id', type=int),
            user_id=current_user.id,
            title=request.form.get('title', '').strip(),
            content=request.form.get('content', '').strip(),
            is_guide=request.form.get('is_guide') == 'on',
            is_tutorial=request.form.get('is_tutorial') == 'on'
        )

        if not post.title or not post.content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('community.create_post'))

        db.session.add(post)
        db.session.commit()

        flash('Post created!', 'success')
        return redirect(url_for('community.view_post', post_id=post.id))

    categories = ForumCategory.query.filter_by(is_active=True).all()
    return render_template('community/create_post.html', categories=categories)


@community_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Edit a forum post"""
    post = ForumPost.query.get_or_404(post_id)

    if post.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('community.view_post', post_id=post_id))

    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        post.updated_at = utcnow()
        db.session.commit()

        flash('Post updated!', 'success')
        return redirect(url_for('community.view_post', post_id=post_id))

    return render_template('community/edit_post.html', post=post)


@community_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a forum post"""
    post = ForumPost.query.get_or_404(post_id)

    if post.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('community.view_post', post_id=post_id))

    db.session.delete(post)
    db.session.commit()

    flash('Post deleted.', 'info')
    return redirect(url_for('community.index'))


@community_bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """Like a forum post"""
    post = ForumPost.query.get_or_404(post_id)

    existing = ForumLike.query.filter_by(
        post_id=post.id, user_id=current_user.id
    ).first()

    if existing:
        db.session.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        db.session.commit()
        return jsonify({'liked': False, 'count': post.like_count})

    like = ForumLike(post_id=post.id, user_id=current_user.id)
    post.like_count += 1
    db.session.add(like)
    db.session.commit()

    return jsonify({'liked': True, 'count': post.like_count})


@community_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add a comment to a post"""
    post = ForumPost.query.get_or_404(post_id)

    content = request.form.get('content', '').strip()
    if not content:
        flash('Comment content is required.', 'danger')
        return redirect(url_for('community.view_post', post_id=post_id))

    if post.is_locked:
        flash('This post is locked.', 'warning')
        return redirect(url_for('community.view_post', post_id=post_id))

    reply_to = request.form.get('reply_to', type=int)

    comment = ForumComment(
        post_id=post.id,
        user_id=current_user.id,
        content=content,
        reply_to_id=reply_to
    )
    post.comment_count += 1
    db.session.add(comment)
    db.session.commit()

    flash('Comment added!', 'success')
    return redirect(url_for('community.view_post', post_id=post_id))


@community_bp.route('/bookmark', methods=['POST'])
@login_required
def toggle_bookmark():
    """Toggle bookmark on a post"""
    post_id = request.form.get('post_id', type=int)
    post = ForumPost.query.get_or_404(post_id)

    existing = UserBookmark.query.filter_by(
        user_id=current_user.id, post_id=post.id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'bookmarked': False})

    bookmark = UserBookmark(user_id=current_user.id, post_id=post.id)
    db.session.add(bookmark)
    db.session.commit()

    return jsonify({'bookmarked': True})


@community_bp.route('/bookmarks')
@login_required
def my_bookmarks():
    """View user's bookmarks"""
    bookmarks = UserBookmark.query.filter_by(
        user_id=current_user.id
    ).order_by(UserBookmark.created_at.desc()).limit(50).all()

    return render_template('community/bookmarks.html', bookmarks=bookmarks)


# API endpoints
@community_bp.route('/api/posts')
def api_posts():
    """API: Get recent posts"""
    page = request.args.get('page', 1, type=int)
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return jsonify({
        'posts': [p.to_dict() for p in posts.items],
        'total': posts.total,
        'pages': posts.pages
    })
