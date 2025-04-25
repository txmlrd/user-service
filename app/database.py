# Step 1: Import the necessary modules
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

# Step 2: Establish a database connection
database_url = f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')}"

engine = create_engine(database_url)  # Create the engine instance

# Define base class
Base = declarative_base()

# Step 3: Define your data model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)  # Store hashed password
    role_id = Column(Integer, nullable=False)  # Foreign key to Role table
    is_verified = Column(Integer, default=0)  # 0 for not verified, 1 for verified
    created_at = Column(DateTime, default=datetime.datetime)
    updated_at = Column(DateTime, default=datetime.datetime, onupdate=datetime.datetime)

class PasswordReset(Base):
    __tablename__ = 'password_resets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # Foreign key to User table
    token = Column(String(100), unique=True, nullable=False)
    expires_at = Column(DateTime, default=datetime.datetime)

# Step 4: Create the database tables
Base.metadata.create_all(engine)  # Pass the engine, not the URL string

# Create a session (if you need to work with the database)
Session = sessionmaker(bind=engine)
session = Session()