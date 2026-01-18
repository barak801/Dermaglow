from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

class AppointmentStatus(enum.Enum):
    PENDING_PAYMENT = 'pending_payment'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    cedula = db.Column(db.String(20))
    current_flow_step = db.Column(db.String(50), default='welcome')
    previous_flow_step = db.Column(db.String(50)) # To track state before escalation
    treatment_interest = db.Column(db.String(100))
    temp_system_hint = db.Column(db.Text) # For transient system messages
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.PENDING_PAYMENT)
    paid = db.Column(db.Boolean, default=False)
    reminder_due_at = db.Column(db.DateTime, nullable=True)
    cancellation_due_at = db.Column(db.DateTime, nullable=True)
    google_event_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'user' or 'agent'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class KnowledgeFile(db.Model):
    __tablename__ = 'knowledge_files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    gemini_uri = db.Column(db.String(255), nullable=False)
    gemini_name = db.Column(db.String(255), nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50)) # e.g. 'Mínimamente Invasivo'
    description = db.Column(db.Text)
    benefits = db.Column(db.Text) # Newline-separated
    duration = db.Column(db.String(100)) # e.g. '60-90 min'
    recovery_time = db.Column(db.String(100)) # e.g. '2-3 días'
    preparation = db.Column(db.Text)
    body_parts = db.Column(db.Text) # Newline-separated or descriptive
    price_info = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
