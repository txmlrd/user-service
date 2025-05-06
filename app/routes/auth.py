from flask import Blueprint, request, jsonify, url_for, render_template
from app.models.user import User
from app.extensions import db, bcrypt, create_access_token, jwt_required
from app.utils.mailer import send_email
from app.utils.serializer import get_serializer
from app.security.redis_handler import blacklist_token

auth_bp = Blueprint('auth', __name__)

# Register
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form
    name, email, password = data.get('name'), data.get('email'), data.get('password')

    if not name or not email or not password:
        return "All fields are required", 400

    if User.query.filter_by(email=email).first():
        return "Email already registered", 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(name=name, email=email, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    token = get_serializer().dumps(email, salt='email-confirm')
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('email_confirmation.html', name=name, confirm_url=confirm_url)
    send_email('Confirm Your Email', email, html=html)

    return "User registered successfully. Please check your email.", 201

# Confirm Email
@auth_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = get_serializer().loads(token, salt='email-confirm', max_age=3600)
    except Exception:
        return "Invalid or expired token", 400

    user = User.query.filter_by(email=email).first_or_404()

    if user.is_verified:
        return "Account already verified", 200
    user.is_verified = 1
    db.session.commit()
    return "Account verified successfully", 200

# Login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.form
    email, password = data.get('email'), data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        if not user.is_verified:
            return "Please verify your email before logging in.", 401
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    return "Invalid credentials", 401

# Logout
@auth_bp.route('/logout')
@jwt_required()
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        jwt_token = auth_header.split(" ")[1]
        blacklist_token(jwt_token)
        return jsonify({"msg": "Successfully logged out"}), 200
    return jsonify({"msg": "Authorization token missing or invalid"}), 400
    
    
# Forgot Password
@auth_bp.route('/reset-password/request', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if user is None:
        return "Email not found", 404

    token = get_serializer().dumps(email, salt='password-reset')
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    send_email('Reset Your Password', email, body=f'Klik link berikut untuk reset password: {reset_url}')

    return "Reset password link sent", 200

# Reset Password
@auth_bp.route('/reset-password/confirm/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = get_serializer().loads(token, salt='password-reset', max_age=3600)
    except Exception:
        return "Invalid or expired token", 400

    user = User.query.filter_by(email=email).first_or_404()

    if request.method == 'POST':
        new_password = request.form.get('password')
        if not new_password:
            return "Password is required", 400
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        return "Password updated successfully", 200

    return '''
        <form method="POST">
            New Password: <input type="password" name="password" required><br>
            <button type="submit">Reset Password</button>
        </form>
    '''
