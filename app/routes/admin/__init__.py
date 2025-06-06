from flask import Blueprint, request, jsonify, url_for, render_template
from app.models.user import User
from app.extensions import db, bcrypt, create_access_token, jwt_required, get_jwt_identity
from app.utils.mailer import send_email
from app.utils.serializer import get_serializer
from app.models.password_reset import PasswordReset
from datetime import datetime, timedelta
import requests
from werkzeug.utils import secure_filename
from app.config import Config

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/get-user', methods=['GET'])
@jwt_required()
def get_all_user():
    role_id = request.args.get('role_id', type=int)
    user_id = request.args.get('user_id', type=int)
    
    if user_id is not None:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({
                "status": "failed",
                "message": "User not found",
                "data": None
            }), 404

        user_data = {
            "id": user.id,
            "uuid": user.uuid,
            "name": user.name,
            "phone": user.phone,
            "profile_picture": user.profile_picture,
            "email": user.email,
            "role_id": user.role_id,
            "is_verified": user.is_verified,
            "face_model_preference": user.face_model_preference,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }

        return jsonify({
            "status": "success",
            "message": "User retrieved successfully",
            "data": user_data
        }), 200

    query = User.query
    if role_id is not None:
        query = query.filter_by(role_id=role_id)

    users = query.all()
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "uuid": user.uuid,
            "name": user.name,
            "phone": user.phone,
            "profile_picture": user.profile_picture,
            "email": user.email,
            "role_id": user.role_id,
            "is_verified": user.is_verified,
            "face_model_preference": user.face_model_preference,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        })

    return jsonify({
        "status": "success",
        "message": "User list retrieved successfully",
        "data": user_list
    }), 200


@admin_bp.route('/search-user', methods=['GET'])
@jwt_required()
def search_user():
    name = request.args.get('name', type=str)
    role_id = request.args.get('role_id', type=int)
    user_id = request.args.get('id', type=int)

    query = User.query

    if user_id:
        query = query.filter_by(id=user_id)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))

    if role_id:
        query = query.filter_by(role_id=role_id)

    users = query.all()
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "uuid": user.uuid,
            "name": user.name,
            "phone": user.phone,
            "profile_picture": user.profile_picture,
            "email": user.email,
            "role_id": user.role_id,
            "is_verified": user.is_verified,
            "face_model_preference": user.face_model_preference,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        })

    return jsonify({
        "status": "success",
        "message": "User search completed successfully",
        "data": user_list
    }), 200


@admin_bp.route('/modify-role', methods=['POST'])
@jwt_required()
def modify_role():
    data = request.get_json()
    uuid = data.get('uuid')
    new_role_id = data.get('role_id')

    if not uuid or new_role_id is None:
        return jsonify({
            "status": "failed",
            "message": "UUID and role_id are required",
            "data": None
        }), 400

    user = User.query.filter_by(uuid=uuid).first()
    if not user:
        return jsonify({
            "status": "failed",
            "message": "User not found",
            "data": None
        }), 404

    user.role_id = new_role_id
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"User {uuid} role updated successfully",
        "data": None
    }), 200


@admin_bp.route('/delete-user/<uuid>', methods=['DELETE'])
@jwt_required()
def delete_user(uuid):
    user = User.query.filter_by(uuid=uuid).first()
    if not user:
        return jsonify({
            "status": "failed",
            "message": "User not found",
            "data": None
        }), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"User {uuid} deleted successfully",
        "data": None
    }), 200

@admin_bp.route('/verify-email-user', methods=['POST'])
@jwt_required()
def verify_email_user():
    data = request.get_json()
    uuid = data.get('uuid')

    if not uuid:
        return jsonify({
            "status": "failed",
            "message": "UUID is required",
            "data": None
        }), 400

    user = User.query.filter_by(uuid=uuid).first()
    if not user:
        return jsonify({
            "status": "failed",
            "message": "User not found",
            "data": None
        }), 404

    user.is_verified = True
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"User email verified successfully",
        "data": None
    }), 200
