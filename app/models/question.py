"""Question and Category Models"""
from datetime import datetime
from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100), default='help-circle')
    color = db.Column(db.String(20), default='#5865F2')
    is_active = db.Column(db.Boolean, default=True)
    question_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', back_populates='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'question_count': self.question_count
        }


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice')
    image_url = db.Column(db.String(500))
    difficulty = db.Column(db.String(20), default='medium')
    explanation = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    times_used = db.Column(db.Integer, default=0)
    correct_rate = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship('Category', back_populates='questions')
    answers = db.relationship('Answer', back_populates='question', lazy='dynamic',
                              cascade='all, delete-orphan')

    def get_correct_answer(self):
        return Answer.query.filter_by(question_id=self.id, is_correct=True).first()

    def to_dict(self, include_answers=True):
        data = {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'image_url': self.image_url,
            'difficulty': self.difficulty,
            'explanation': self.explanation,
            'category': self.category.name if self.category else None
        }
        if include_answers:
            data['answers'] = [a.to_dict() for a in self.answers]
        return data


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    question = db.relationship('Question', back_populates='answers')

    def to_dict(self):
        return {
            'id': self.id,
            'answer_text': self.answer_text,
            'is_correct': self.is_correct
        }
