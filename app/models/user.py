from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True) 
    profile_picture = db.Column(db.String(100), nullable=True) 
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # hashed password
    role_id = db.Column(db.Integer, nullable=False, default=1) 
    is_verified = db.Column(db.Boolean, default=False)  
    face_model_preference = db.Column(db.Integer, nullable=True, default=1) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

