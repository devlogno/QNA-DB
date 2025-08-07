# models/analytics_models.py
import datetime
from extensions import db

class ExamSession(db.Model):
    """
    Stores the results of a single quiz or practice test taken by a user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken_seconds = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    
    settings = db.Column(db.JSON, nullable=True) 
    
    question_ids_json = db.Column(db.JSON, nullable=True)

    user = db.relationship('User', backref='exam_sessions')
    answers = db.relationship('ExamAnswer', backref='exam_session', lazy='dynamic', cascade="all, delete-orphan")

    @property
    def accuracy(self):
        # This is a general accuracy, which might be misleading for mixed exams.
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 2)

    # --- NEW: Property for accurate MCQ-based accuracy ---
    @property
    def mcq_accuracy(self):
        """Calculates accuracy based only on the number of MCQs in the quiz."""
        num_mcq = self.settings.get('num_mcq', 0)
        if self.settings.get('question_type') == 'MCQ':
            num_mcq = self.total_questions
        
        if num_mcq == 0:
            return 0
        
        # Ensure score isn't negative for accuracy calculation
        display_score = max(0, self.score)
        return round((display_score / num_mcq) * 100, 2)


class ExamAnswer(db.Model):
    """
    Logs an individual answer within an exam session for detailed review.
    """
    id = db.Column(db.Integer, primary_key=True)
    exam_session_id = db.Column(db.Integer, db.ForeignKey('exam_session.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_answer = db.Column(db.String(1), nullable=True) # For MCQs (A, B, C, D)
    is_correct = db.Column(db.Boolean, nullable=False)
    
    question = db.relationship('Question')
