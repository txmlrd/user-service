from flask import Flask, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

#test

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

# Endpoint profile
@app.route('/profile')
def profile():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role_id': user.role_id,
            'is_verified': user.is_verified,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
        }
        return jsonify(user_data)

    return jsonify({'error': 'Unauthorized'}), 401

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
        return redirect(url_for('profile'))
    else:
        return "Invalid credentials", 401

@app.route('/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return "Unauthorized", 401

    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    data = request.form  # atau request.json kalo kirim JSON
    user.name = data.get('name', user.name)  # fallback ke nama lama kalau kosong

    try:
        db.session.commit()
        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role_id": user.role_id,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        }), 200
    except:
        db.session.rollback()
        return "Failed to update profile", 500

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_profile(id):
    if 'user_id' not in session:
        return "Unauthorized", 401

    if session['user_id'] != id:
        return "Forbidden: You can only delete your own profile", 403

    user = User.query.get_or_404(id)
    
    db.session.delete(user)
    db.session.commit()
    session.clear()
    
    return "Profile deleted successfully", 200

    

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
