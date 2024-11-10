# reset_db.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Define User model here to avoid importing
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiration = db.Column(db.DateTime)

def reset_database():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating new tables...")
        db.create_all()
        
        try:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='farmprojecttufail@gmail.com',
                is_active=True,
                created_at=datetime.utcnow()
            )
            admin.password_hash = generate_password_hash('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
            
            user = User.query.first()
            print(f"Verified user created with email: {user.email}")
            
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    print("Starting database reset...")
    reset_database()
    print("Database reset complete!")
