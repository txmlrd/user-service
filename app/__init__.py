from flask import Flask
from .extensions import db, bcrypt, mail, migrate, jwt
from .config import Config
from .routes.auth import auth_bp
from .routes.user import user_bp
from .routes.internal import internal_bp
from .routes.admin import admin_bp
from .models.user import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(internal_bp, url_prefix='/internal')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/')
    def index():
        return 'User Service Running!'

    return app


