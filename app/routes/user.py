from flask import Blueprint, session, jsonify, request
from models.user import User
from app import db

user_bp = Blueprint('user', __name__)

# Profile
@user_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

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

# Update Profile
@user_bp.route('/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return "Unauthorized", 401

    user = User.query.get_or_404(session['user_id'])
    data = request.form
    user.name = data.get('name', user.name)

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

# Delete Profile
@user_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_profile(id):
    if 'user_id' not in session:
        return "Unauthorized", 401

    if session['user_id'] != id:
        return "Forbidden", 403

    user = User.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()
    session.clear()

    return "Profile deleted successfully", 200
