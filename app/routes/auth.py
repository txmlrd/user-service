from flask import Blueprint, request, jsonify, url_for, render_template
from app.models.user import User
from app.extensions import db, bcrypt, create_access_token, jwt_required, get_jwt_identity
from app.utils.mailer import send_email
from app.utils.serializer import get_serializer
from datetime import datetime, timedelta
import requests
from werkzeug.utils import secure_filename
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
    if face and face.filename and face.stream.read()  
]
    for face in face_references:
        face.stream.seek(0)

    if not name or not email or not password or not phone:
        return jsonify({"msg": "All fields are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already registered"}), 409

    if User.query.filter_by(phone=phone).first():
        return jsonify({"msg": "Phone number already registered"}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        new_user = User(name=name, email=email, password=hashed_password, phone=phone)
        db.session.add(new_user)
        db.session.flush() 

        uuid = new_user.uuid
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

        db.session.commit()

        # mengirim email konfirmasi
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
        return render_template('email_verification_result.html', status='invalid')

    user = User.query.filter_by(email=email).first_or_404()

    if user.is_verified:
        return render_template('email_verification_result.html', status='already_verified')

    user.is_verified = 1
    db.session.commit()
    return render_template('email_verification_result.html', status='success')


    


