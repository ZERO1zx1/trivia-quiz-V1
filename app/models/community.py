"""Community / Forum System Models"""
from datetime import datetime
from app.extensions import db


class ForumCategory(db.Model):
    __tablename__ = 'forum_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    icon = db.Column(db.String(50), default='')
    color = db.Column(db.String(7), default='#7C3AED')
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship('ForumPost', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<ForumCategory {self.name}>'


class ForumPost(db.Model):
    __tablename__ = 'forum_posts'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    is_guide = db.Column(db.Boolean, default=False)
    is_tutorial = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('ForumCategory', back_populates='posts')
    user = db.relationship('User', backref='forum_posts')
    comments = db.relationship('ForumComment', back_populates='post', lazy='dynamic')
    likes = db.relationship('ForumLike', back_populates='post', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'user': self.user.username if self.user else 'Unknown',
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'view_count': self.view_count,
            'is_pinned': self.is_pinned,
            'is_guide': self.is_guide,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<ForumPost {self.title}>'


class ForumComment(db.Model):
    __tablename__ = 'forum_comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    is_edited = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    reply_to_id = db.Column(db.Integer, db.ForeignKey('forum_comments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    edited_at = db.Column(db.DateTime, nullable=True)

    post = db.relationship('ForumPost', back_populates='comments')
    user = db.relationship('User', backref='forum_comments')

    def __repr__(self):
        return f'<ForumComment post={self.post_id} user={self.user_id}>'


class ForumLike(db.Model):
    __tablename__ = 'forum_likes'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    post = db.relationship('ForumPost', back_populates='likes')
    user = db.relationship('User', backref='forum_likes')

    def __repr__(self):
        return f'<ForumLike post={self.post_id} user={self.user_id}>'


class UserBookmark(db.Model):
    __tablename__ = 'user_bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bookmarks')
    post = db.relationship('ForumPost', backref='bookmarkers')

    def __repr__(self):
        return f'<UserBookmark user={self.user_id}>'
