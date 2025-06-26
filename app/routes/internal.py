from app.models.user import User
from flask import Blueprint, request, jsonify
from app.extensions import db
from dotenv import load_dotenv
import os

load_dotenv() 

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
        "uuid": user.uuid,
    }

    return jsonify(user_data), 200

@internal_bp.route('/user-by-id', methods=['GET'])
def get_user_by_id():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "id": user.id,
        "password": user.password,
        "email": user.email,
        "face_model_preference": user.face_model_preference,
        "is_verified": user.is_verified,
        "role_id": user.role_id,
        "uuid": user.uuid
    }

    return jsonify(user_data), 200

@internal_bp.route('/user-by-uuid', methods=['GET'])
def get_user_by_uuid():
    uuid = request.args.get('uuid')
    if not uuid:
        return jsonify({"error": "UUID is required"}), 400

    user = User.query.filter_by(uuid=uuid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "id": user.id,
        "password": user.password,
        "email": user.email,
        "face_model_preference": user.face_model_preference,
        "is_verified": user.is_verified,
        "role_id": user.role_id,
        "uuid": user.uuid
    }

    return jsonify(user_data), 200

@internal_bp.route('/users/<email>/password', methods=['PATCH'])
def update_password(email):
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {os.getenv('RESET_PASSWORD_SECRET')}":
        return jsonify({"error": "Unauthorized"}), 400
    data = request.get_json()
    new_password = data.get("new_password")

    if not new_password:
        return jsonify({"error": "Missing new password"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 400

    user.password = new_password
    db.session.commit()
    return jsonify({"message": "Password updated successfully"}), 200



