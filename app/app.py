from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')


app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Inisialisasi extension
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Model User
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role_id = db.Column(db.Integer, nullable=False, default=1)
    is_verified = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Endpoint dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return f"Welcome user ID: {session['user_id']}, your name is {User.query.get(session['user_id']).name}, role ID: {User.query.get(session['user_id']).role_id}, verified: {User.query.get(session['user_id']).is_verified}, created at: {User.query.get(session['user_id']).created_at}, updated at: {User.query.get(session['user_id']).updated_at}"
    return "Unauthorized", 401

# Endpoint register
@app.route('/register', methods=['POST'])
def register():
    data = request.form
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return "All fields are required", 400

    # Cek jika email sudah digunakan
    if User.query.filter_by(email=email).first():
        return "Email already registered", 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
    )
    
    db.session.add(new_user)
    db.session.commit()
    return "User registered successfully", 201

# Endpoint login
@app.route('/login', methods=['POST'])
def login():
    data = request.form
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    else:
        return "Invalid credentials", 401

@app.route('/logout')
def logout():
    if session.get('user_id') is None:
        return "Already logged out", 400
    session.clear()
    return "Logged out successfully", 200
    
    
# Jalankan app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
