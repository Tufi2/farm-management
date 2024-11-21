# app/routes/health_records/__init__.py

from flask import Blueprint

bp = Blueprint('health_records', __name__, url_prefix='/health-records')

# Import routes after blueprint creation to avoid circular imports
from app.routes.health_records import views, downloads, sheep, cattle, goat, chicken