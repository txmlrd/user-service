from app.models.user import User
from app.models.password_reset import PasswordReset
from flask import Blueprint, request, jsonify

internal_bp = Blueprint('internal', __name__)
@internal_bp.route('/user-by-email', methods=['GET'])
def get_user_by_email():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "id": user.id,
        "password": user.password,
        "email": user.email,
        "face_model_preference": user.face_model_preference,
        "is_verified": user.is_verified,
        "role_id": user.role_id,
    }

    return jsonify(user_data), 200




