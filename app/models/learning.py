"""Learning System Models"""
from datetime import datetime
from app.extensions import db, utcnow


class Flashcard(db.Model):
    __tablename__ = 'flashcards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    front_text = db.Column(db.Text, nullable=False)
    back_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), default='')
    difficulty = db.Column(db.String(20), default='medium')
    times_reviewed = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    incorrect_count = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.DateTime, nullable=True)
    next_review = db.Column(db.DateTime, nullable=True)
    is_bookmarked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User', backref='flashcards')

    def __repr__(self):
        return f'<Flashcard user={self.user_id} category={self.category}>'


class StudyNote(db.Model):
    __tablename__ = 'study_notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    category = db.Column(db.String(100), default='')
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    user = db.relationship('User', backref='study_notes')

    def __repr__(self):
        return f'<StudyNote user={self.user_id} title={self.title}>'


class ExamAttempt(db.Model):
    __tablename__ = 'exam_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), default='medium')
    total_questions = db.Column(db.Integer, default=10)
    correct_answers = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0.0)
    duration_seconds = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    certificate_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    user = db.relationship('User', backref='exam_attempts')

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'score': self.score,
            'correct_answers': self.correct_answers,
            'total_questions': self.total_questions,
            'passed': self.passed,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<ExamAttempt user={self.user_id} category={self.category} score={self.score}>'
