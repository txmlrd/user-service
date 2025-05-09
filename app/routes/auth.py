from flask import Blueprint, request, jsonify, url_for, render_template
from app.models.user import User
from app.extensions import db, bcrypt, create_access_token, jwt_required, get_jwt_identity
from app.utils.mailer import send_email
from app.utils.serializer import get_serializer
from app.models.password_reset import PasswordReset
from datetime import datetime, timedelta
import requests
from werkzeug.utils import secure_filename
from app.functions.get_user_requests_password import get_user_request_password
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
    
@auth_bp.route('/reset-password/request', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"msg": "Email not found"}), 404

    check_token, status = get_user_request_password(user.id)
    
    if status == 200:
        minutes_left = int((check_token.expires_at - datetime.utcnow()).total_seconds()) // 60
        reset_url = url_for('auth.reset_password', token=check_token.token, _external=True)
        send_email(
            'Reset Your Password',
            email,
            body=f'Link masih berlaku sekitar {minutes_left} menit.\nKlik link berikut untuk reset password: {reset_url}'
        )
        return jsonify({"msg": "Reset password link resent, please check your email!"}), 200

    # Token expired atau tidak ditemukan → buat baru
    token = get_serializer().dumps(email, salt='password-reset')
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    send_email('Reset Your Password', email, body=f'Klik link berikut untuk reset password: {reset_url}')

    now = datetime.utcnow()
    save_token = PasswordReset(
        user_id=user.id,
        token=token,
        created_at=now,
        expires_at=now + timedelta(minutes=15),
        is_reset=False
    )
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
    user_token = PasswordReset.query.filter_by(token=token).first()
    if not user:
        return render_template("reset_password.html", error="User not found")
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password:
            return render_template("reset_password.html", error="Password is required")
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        user_token.is_reset = True
        db.session.commit()  
        return render_template("reset_password.html", success=True)


    if user_token.is_reset == True:
        return render_template("reset_password.html", already_used=True)
    
    if user_token.expires_at < datetime.utcnow():
        return render_template("reset_password.html", expired=True)
    return render_template("reset_password.html")


