from flask import Blueprint, session, jsonify, request
from app.models.user import User
from app.extensions import jwt_required, get_jwt_identity
from app import db

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
        'name': user.name,
        'phone': user.phone,
        'profile_picture': user.profile_picture,
        'email': user.email,
        'role_id': user.role_id,
        'is_verified': user.is_verified,
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
                "name": user.name,
                "phone": user.phone,
                "profile_picture": user.profile_picture,
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
