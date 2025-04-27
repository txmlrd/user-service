from flask import Flask
from extensions import db, bcrypt, mail
from config import Config
from routes.auth import auth_bp
from routes.user import user_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    with app.app_context():
        db.create_all()  

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    @app.route('/')
    def index():
        return 'User Service Running!'

    return app


