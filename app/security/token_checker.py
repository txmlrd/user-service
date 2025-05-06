from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from app.security.redis_handler import is_token_blacklisted
from flask import request

def check_token_blacklisted(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Ambil JWT dari header Authorization
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header.split(" ")[1]
            if is_token_blacklisted(jwt_token):
                return jsonify({"msg": "Token is blacklisted. Please log in again."}), 401
        return fn(*args, **kwargs)
    return wrapper

