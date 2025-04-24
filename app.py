from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime

app = Flask(__name__)
app.secret_key = 'gungadhisanjaya'

# Konfigurasi koneksi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/user_service'
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
        return f"Welcome user ID: {session['user_id']}"
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
        role_id=1,
        is_verified=0
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

# Jalankan app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
