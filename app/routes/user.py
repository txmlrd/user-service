from flask import Blueprint, session, jsonify, request, url_for
from app.models.user import User
from app.extensions import jwt_required, get_jwt_identity
from app import db
import requests
from werkzeug.utils import secure_filename
from app.config import Config
from app.utils.serializer import get_serializer
from app.utils.mailer import send_email

user_bp = Blueprint('user', __name__)

# Profile
@user_bp.route('/profile')
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_data = {
        'id': user.id,
        'uuid': user.uuid,
        'name': user.name,
        'phone': user.phone,
        'profile_picture': user.profile_picture,
        'email': user.email,
        'role_id': user.role_id,
        'is_verified': user.is_verified,
        'face_model_preference': user.face_model_preference,
        'created_at': user.created_at.isoformat(),
        'updated_at': user.updated_at.isoformat()
    }
    return jsonify(user_data)

# Update Profile
@user_bp.route('/update', methods=['POST'])
@jwt_required()
# @check_device_token
def update_profile():
    current_user_id = get_jwt_identity()
    
    user = User.query.get(current_user_id)
    data = request.get_json()
    user.name = data.get('name', user.name)
    user.phone = data.get('phone', user.phone)

    try:
        db.session.commit()
        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "uuid": user.uuid,
                "name": user.name,
                "phone": user.phone,
                "profile_picture": user.profile_picture,
                "face_model_preference": user.face_model_preference,
                "email": user.email,
                "role_id": user.role_id,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        }), 200
    except:
        db.session.rollback()
        return jsonify({
            "error": "Failed to update profile"
        }), 500
        
        
@user_bp.route('/update/email/request', methods=['POST'])
@jwt_required()
def update_email():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    new_email = request.get_json().get('email')

    if not new_email:
        return jsonify({"msg": "Email baru harus disediakan"}), 400

    if User.query.filter_by(email=new_email).first():
        return jsonify({"msg": "Email ini sudah digunakan user lain"}), 400

    # Token berisi user_id dan email baru
    token_data = {'user_id': user.id, 'new_email': new_email}
    token = get_serializer().dumps(token_data, salt='email-change')

    confirm_url = url_for('user.change_email', token=token, _external=True)

    # 1. Kirim link ke email lama
    send_email(
        subject='Konfirmasi Pergantian Email',
        recipient=user.email,
        body=f'Klik link berikut untuk menyetujui pergantian email akunmu ke {new_email}:\n\n{confirm_url}'
    )

    # 2. Kirim notifikasi ke email baru
    send_email(
        subject='Permintaan Pergantian Email',
        recipient=new_email,
        body=f'Email ini diminta untuk menjadi alamat baru akun milik {user.email}. '
             f'Jika kamu tidak merasa melakukan ini, abaikan saja.'
    )

    return jsonify({"msg": "Link konfirmasi telah dikirim ke email lama, dan notifikasi ke email baru."}), 200


    
@user_bp.route('/update/email/confirm/<token>', methods=['GET'])
def change_email(token):
    try:
        data = get_serializer().loads(token, salt='email-change', max_age=3600)
        user_id = data['user_id']
        new_email = data['new_email']
    except Exception:
        return jsonify({"msg": "Token tidak valid atau telah kedaluwarsa"}), 400

    user = User.query.get_or_404(user_id)

    # Cek ulang agar tidak bentrok email
    if User.query.filter_by(email=new_email).first():
        return jsonify({"msg": "Email ini sudah digunakan oleh user lain"}), 400

    old_email = user.email
    user.email = new_email
    db.session.commit()

    # 🔔 Kirim notifikasi ke email lama
    send_email(
        subject='Email Akun Telah Diganti',
        recipient=old_email,
        body=f'Email akunmu telah berhasil diganti ke {new_email}.\n\nJika kamu tidak melakukan ini, segera hubungi admin.'
    )

    # 🔔 Kirim notifikasi ke email baru
    send_email(
        subject='Selamat, Email Akun Telah Aktif',
        recipient=new_email,
        body=f'Email ini sekarang telah digunakan sebagai alamat akun kamu. Jika ini bukan kamu, segera hubungi admin.'
    )

    return jsonify({"msg": "Email berhasil diperbarui dan notifikasi telah dikirim."}), 200




@user_bp.route('/delete/<int:id>', methods=['DELETE'])
@jwt_required()
# @check_device_token
def delete_profile(id):
    current_user_id = get_jwt_identity()

    if int(current_user_id) != id:
        return jsonify({'error': 'Forbidden'}), 403

    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'msg': 'Profile deleted successfully'}), 200

@user_bp.route('/update/face-reference', methods=['POST'])
@jwt_required()
# @check_device_token
def update_face_reference():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user_id = user.id
    face_references = request.files.getlist('images')
    if not face_references:
        return jsonify({"error": "No face references provided"}), 400
    files = []
    for face in face_references:
        filename = secure_filename(face.filename)
        files.append(('images', (filename, face, face.mimetype)))
    data = {'user_id': user_id}
    try:
        response = requests.post(f"{Config.AUTH_SERVICE_URL}/upload-face", data=data, files=files)
        # Cek response dari API /upload-face
        if response.status_code == 200:
            return jsonify({"message": "Face reference updated successfully"}), 200
        else:
            return jsonify({"error": "Failed to upload face reference", "details": response.json()}), 500
    except requests.exceptions.RequestException as e:
        # Jika gagal menghubungi user service
        return jsonify({"error": "User Service unavailable", "details": str(e)}), 503
    
@user_bp.route('/update/face-model-preference', methods=['POST'])
@jwt_required()
# @check_device_token
def update_face_model_preference():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.form
    user.face_model_preference = data.get('face_model_preference', user.face_model_preference)

    try:
        db.session.commit()
        return jsonify({
            "message": "Face model preference updated successfully",
            "user": {
                "id": user.id,
                "uuid": user.uuid,
                "name": user.name,
                "face_model_preference": user.face_model_preference,
            }
        }), 200
    except:
        db.session.rollback()
        return jsonify({
            "error": "Failed to update face model preference"
        }), 500