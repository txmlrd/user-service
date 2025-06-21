import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from app import create_app, db
from app.models.user import User
from app.extensions import bcrypt
import os
import uuid

app = create_app()

with app.app_context():
    default_name = os.getenv("ADMIN_NAME")
    default_email = os.getenv("ADMIN_EMAIL")
    default_password = os.getenv("ADMIN_PASSWORD")

    existing_admin = User.query.filter_by(email=default_email).first()
    if existing_admin:
        print(f"⚠️ Admin dengan email '{default_email}' sudah ada.")
    else:
        new_admin = User(
            uuid=str(uuid.uuid4()),
            name=default_name,
            email=default_email,
            password=bcrypt.generate_password_hash(default_password).decode('utf-8'),
            role_id=1, 
            is_verified=True,
            phone=08213213545
        )
        db.session.add(new_admin)
        db.session.commit()
        print(f"✅ Admin user '{default_email}' berhasil dibuat.")
