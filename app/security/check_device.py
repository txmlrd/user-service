from functools import wraps
from flask_jwt_extended import get_jwt
from flask import jsonify
from app.extensions import redis_client, get_jwt_identity

def check_device_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ambil user_id dari JWT token yang ada
        user_id = get_jwt_identity()

        # Ambil current_jti (token JTI saat ini) dari JWT
        current_jti = get_jwt()['jti']

        # Cek apakah ada token sebelumnya yang disimpan di Redis
        stored_jti = redis_client.get(f"user_active_token:{user_id}")

        # Jika ada token yang tersimpan di Redis dan berbeda dengan current JTI, berarti login di perangkat lain
        if stored_jti and stored_jti.decode() != current_jti:
            return jsonify({"msg": "Another device is logged in"}), 403

        return f(*args, **kwargs)

    return decorated_function
