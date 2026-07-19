from datetime import datetime
from app.extensions import db

class UserQuestion(db.Model):
    __tablename__ = 'user_questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(255), nullable=False)
    wrong_answer1 = db.Column(db.String(255), nullable=False)
    wrong_answer2 = db.Column(db.String(255), nullable=False)
    wrong_answer3 = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    difficulty = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('submitted_questions', lazy='dynamic'))
    category = db.relationship('Category')

    def to_dict(self):
        return {
            'id': self.id,
            'question_text': self.question_text,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }