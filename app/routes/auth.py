from flask import Blueprint, request, jsonify, url_for, render_template
from app.models.user import User
from app.extensions import db, bcrypt, create_access_token, jwt_required, get_jwt_identity
from app.utils.mailer import send_email
from app.utils.serializer import get_serializer
from app.models.password_reset import PasswordReset
from datetime import datetime, timedelta
import requests
from werkzeug.utils import secure_filename
# from app.security.redis_handler import blacklist_token
# from app.security.check_device import check_device_token

auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form
    name, email, password, phone = data.get('name'), data.get('email'), data.get('password'), data.get('phone')
    
    # Ambil face_reference yang merupakan file gambar
    face_references = request.files.getlist('face_reference')

    if not name or not email or not password or not phone or len(face_references) != 3:
        return jsonify({"msg"  "All fields are required and exactly 3 face images must be provided"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Menambahkan user baru ke database
    new_user = User(name=name, email=email, password=hashed_password, phone=phone)
    db.session.add(new_user)
    db.session.commit()
    
    user_id = new_user.id

    # Dapatkan user_id dari user yang baru saja didaftarkan
    files = []
    for face in face_references:
        filename = secure_filename(face.filename)
        files.append(('images', (filename, face, face.mimetype)))

    data = {'user_id': user_id}


    try:
        response = requests.post("http://face-recognition:5000/upload-face", data=data, files=files)

        # Cek response dari API /upload-face
        if response.status_code == 200:
            # Jika upload face references berhasil, kirimkan token konfirmasi email
            token = get_serializer().dumps(email, salt='email-confirm')
            confirm_url = url_for('auth.confirm_email', token=token, _external=True)
            html = render_template('email_confirmation.html', name=name, confirm_url=confirm_url)
            send_email('Confirm Your Email', email, html=html)

            return jsonify({"message": "User registered and face reference uploaded, please check email"}), 201
        else:
            # Jika gagal upload face reference, rollback user yang baru dibuat
            db.session.rollback()
            return jsonify({"error": "Failed to upload face reference", "details": response.json()}), 500

    except requests.exceptions.RequestException as e:
        # Jika gagal menghubungi user service
        return jsonify({"error": "User Service unavailable", "details": str(e)}), 503


# Confirm Email
@auth_bp.route('/verify-email/<token>')
def confirm_email(token):
    try:
        email = get_serializer().loads(token, salt='email-confirm', max_age=3600)
    except Exception:
        return jsonify({"msg": "Invalid or expired token"}), 400

    user = User.query.filter_by(email=email).first_or_404()

    if user.is_verified:
        return jsonify({"msg": "Email already verified"}), 400
    user.is_verified = 1
    db.session.commit()
    return jsonify({"msg": "Email verified successfully"}), 200

# # Login
# @auth_bp.route('/login', methods=['POST'])
# def login():
#     data = request.form
#     email, password = data.get('email'), data.get('password')

#     user = User.query.filter_by(email=email).first()

#     if user and bcrypt.check_password_hash(user.password, password):
#         if not user.is_verified:
#             return "Please verify your email before logging in.", 401
#         access_token = create_access_token(identity=str(user.id))
#         return jsonify(access_token=access_token), 200
#     return "Invalid credentials", 401

# @auth_bp.route('/login/face', methods=['POST'])
# def login_face():
#     data = request.form
#     email = data.get('email')
#     face = request.files.get('face_image')
    
#     if not email or not face:
#         return "All fields are required", 400

#     # Cari user berdasarkan username atau email
#     user = User.query.filter((User.email == email)).first()
#     if not user:
#         return "User not found", 404

#     user_id = user.id

#     # Kirim ke Face Recognition Service
#     filename = secure_filename(face.filename)
#     files = {'image': (filename, face.stream, face.mimetype)}
#     payload = {'user_id': user_id}
    
#     try:
#         response = requests.post("http://face-recognition:5000/verify", data=payload, files=files)
        
#         if response.status_code == 200:
#             access_token = create_access_token(identity=str(user_id))
#             return jsonify(access_token=access_token), 200
#         else:
#             return jsonify({"error": "Face recognition failed", "details": response.json()}), 401

#     except requests.exceptions.RequestException as e:
#         return jsonify({"error": "Face Recognition Service unavailable", "details": str(e)}), 503


# # Logout
# @auth_bp.route('/logout', methods=['GET'])
# @jwt_required() 
# # @check_device_token
# def logout():
#     try :
#         user = get_jwt_identity()
#         return jsonify({"user_id": user}), 200
#     except Exception as e:
#         return jsonify({"msg": "Token is invalid"}), 401
    
    
# Forgot Password
@auth_bp.route('/reset-password/request', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"msg": "Email not found"}), 404

    token = get_serializer().dumps(email, salt='password-reset')
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    send_email('Reset Your Password', email, body=f'Klik link berikut untuk reset password: {reset_url}')
    
    created_at = datetime.utcnow()
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    save_token = PasswordReset(user_id=user.id, token=token, expires_at=expires_at, created_at=created_at)
    db.session.add(save_token)
    db.session.commit()
    
    return jsonify({"msg": "Reset password request success, please check your email!"}), 200

@auth_bp.route('/reset-password/confirm/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = get_serializer().loads(token, salt='password-reset', max_age=900)
    except Exception:
        return render_template("reset_password.html", error="Invalid or expired token")

    user = User.query.filter_by(email=email).first()
    if not user:
        return render_template("reset_password.html", error="User not found")

    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password:
            return render_template("reset_password.html", error="Password is required")
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        return render_template("reset_password.html", success=True)

    # Jika GET
    return render_template("reset_password.html")


