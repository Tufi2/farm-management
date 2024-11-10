import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Basic Flask configuration
    SECRET_KEY = 'dev-key-please-change'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///farm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    # Email configurations
    MAIL_SERVER = 'smtp.gmail.com'  # or your email server
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-app-password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')
    