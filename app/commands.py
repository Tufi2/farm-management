import click
from flask.cli import with_appcontext
from app import db
from app.models.user import User

@click.command('create-admin')
@with_appcontext
def create_admin():
    """Create an admin user"""
    username = 'admin'
    password = 'admin123'
    
    if User.query.filter_by(username=username).first():
        print('Admin user already exists!')
        return

    user = User(username=username)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    print('Admin user created successfully!')