from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Import models here
    from app.models.user import User
    from app.models.animal import Animal, HealthRecord  # Add this line to import health record model

    with app.app_context():
        # Register blueprints
        from app.routes import main, auth, animals, inventory, health_records  # Add health_records import
        app.register_blueprint(main.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(animals.bp)
        app.register_blueprint(inventory.bp)
        app.register_blueprint(health_records.bp)  # Register health_records blueprint

        # Create database tables
        db.create_all()

    # Register commands
    from app.commands import create_admin
    app.cli.add_command(create_admin)

    return app