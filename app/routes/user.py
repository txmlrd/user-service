from flask import Blueprint, session, jsonify, request
from app.models.user import User
from app.extensions import jwt_required, get_jwt_identity
from app import db
import requests
from werkzeug.utils import secure_filename
from app.config import Config

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
    data = request.form
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
        
        
@user_bp.route('/update/email', methods=['POST'])
@jwt_required()
# @check_device_token
def update_email():
    current_user_id = get_jwt_identity()
    
    user = User.query.get(current_user_id)
    data = request.form
    user.email = data.get('email', user.email)

    try:
        db.session.commit()
        return jsonify({
            "message": "Email updated successfully",
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
            "error": "Failed to update email"
        }), 500


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
    user = User.query.get(current_user_id)
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