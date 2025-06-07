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
from app.config import Config

auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    face_references = [
    face for face in request.files.getlist('face_reference')
    if face and face.filename and face.stream.read()  # cek ada isi
]
# Kembalikan posisi pointer stream ke awal (wajib)
    for face in face_references:
        face.stream.seek(0)



    # Validasi form
    if not name or not email or not password or not phone:
        return jsonify({"msg": "All fields are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 409

    if User.query.filter_by(phone=phone).first():
        return jsonify({"msg": "Phone number already registered"}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        # Buat user baru
        new_user = User(name=name, email=email, password=hashed_password, phone=phone)
        db.session.add(new_user)
        db.session.flush()  # Dapatkan UUID sebelum commit

        uuid = new_user.uuid

        # Jika ada face_reference, kirim ke auth service
        if face_references:
            files = []
            for face in face_references:
                filename = secure_filename(face.filename)
                files.append(('images', (filename, face, face.mimetype)))

            upload_data = {'uuid': uuid}
            try:
                response = requests.post(f"{Config.AUTH_SERVICE_URL}/upload-face", data=upload_data, files=files)
                if response.status_code != 200:
                    db.session.rollback()
                    return jsonify({"error": "Failed to upload face reference", "details": response.json()}), 500
            except requests.exceptions.RequestException as e:
                db.session.rollback()
                return jsonify({"error": "Auth service unavailable", "details": str(e)}), 503

        # Commit setelah semua sukses
        db.session.commit()

        # Kirim email konfirmasi
        try:
            token = get_serializer().dumps(email, salt='email-confirm')
            confirm_url = f"{Config.API_GATEWAY_URL}/user/verify-email/{token}"
            html = render_template('email_confirmation.html', name=name, confirm_url=confirm_url)
            send_email('Confirm Your Email', email, html=html)

            msg = "User registered"
            if face_references:
                msg += " and face reference uploaded"
            msg += ", please check email for confirmation"

            return jsonify({"message": msg}), 201

        except Exception as e:
            return jsonify({"error": "Failed to send confirmation email", "details": str(e)}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed", "details": str(e)}), 500
        
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
    email = request.get_json().get('email')
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"msg": "Email not found"}), 404

    check_token, status = get_user_request_password(user.uuid)
    
    if status == 200:
        minutes_left = int((check_token.expires_at - datetime.utcnow()).total_seconds()) // 60
        reset_url = f"{Config.API_GATEWAY_URL}/user/reset-password/confirm/{check_token.token}"
        send_email(
            'Reset Your Password',
            email,
            body=f'Link masih berlaku sekitar {minutes_left} menit.\nKlik link berikut untuk reset password: {reset_url}'
        )
        return jsonify({"msg": "Reset password link resent, please check your email!", "reset_url" : reset_url}), 200

    # Token expired atau tidak ditemukan → buat baru
    token = get_serializer().dumps(email, salt='password-reset')
    reset_url = f"{Config.API_GATEWAY_URL}/user/reset-password/confirm/{token}"
    # reset_url = url_for('auth.reset_password', token=token, _external=True)
    send_email('Reset Your Password', email, body=f'Klik link berikut untuk reset password: {reset_url}')

    now = datetime.utcnow()
    save_token = PasswordReset(
        uuid=user.uuid,
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


