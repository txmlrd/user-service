from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from app.security.redis_handler import is_token_blacklisted_by_jti

db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()
jwt = JWTManager()
create_access_token = create_access_token
jwt_required = jwt_required
get_jwt_identity = get_jwt_identity

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    return is_token_blacklisted_by_jti(jti)
