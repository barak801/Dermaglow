from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False) # Twilio From ID
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    message_count = db.Column(db.Integer, default=0)
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(10), nullable=False) # 'user' or 'agent'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class KnowledgeBase(db.Model):
    __tablename__ = 'knowledge_base'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_uri = db.Column(db.String(255), nullable=False) # Gemini File URI
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class LeadSummary(db.Model):
    __tablename__ = 'lead_summaries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    summary_text = db.Column(db.Text, nullable=False)
    key_interests = db.Column(db.String(255))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
