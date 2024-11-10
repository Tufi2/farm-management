from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from app.models.user import User
from app import db, mail
from datetime import datetime, timedelta
import re
import secrets

bp = Blueprint('auth', __name__)

def is_valid_password(password):
    """Check if password meets security requirements"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # At least one uppercase
        return False
    if not re.search(r"[a-z]", password):  # At least one lowercase
        return False
    if not re.search(r"\d", password):      # At least one digit
        return False
    return True

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('This account has been deactivated. Please contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
            
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'danger')
            return redirect(url_for('auth.register'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address', 'danger')
            return redirect(url_for('auth.register'))

        if not is_valid_password(password):
            flash('Password must be at least 8 characters long and contain uppercase, lowercase, and numbers', 'danger')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('auth.register'))

        try:
            user = User(
                username=username, 
                email=email,
                created_at=datetime.utcnow(),
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            print(f"Processing password reset for email: {email}")
            
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                flash('Please enter a valid email address', 'danger')
                return redirect(url_for('auth.forgot_password'))

            user = User.query.filter_by(email=email).first()
            print(f"User found: {user is not None}")
            
            if user:
                try:
                    print("Generating token...")
                    token = secrets.token_urlsafe(32)
                    user.reset_token = token
                    user.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
                    db.session.commit()
                    print("Token saved to database")
                    
                    reset_url = url_for('auth.reset_password', token=token, _external=True)
                    print(f"Reset URL generated: {reset_url}")
                    
                    msg = Message('Password Reset Request',
                                recipients=[user.email],
                                sender=current_app.config['MAIL_DEFAULT_SENDER'])
                    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.

This link will expire in 1 hour.
'''
                    print("Attempting to send email...")
                    mail.send(msg)
                    print("Email sent successfully")
                    
                    flash('Password reset instructions have been sent to your email.', 'info')
                    return redirect(url_for('auth.login'))
                    
                except Exception as inner_e:
                    print(f"Inner error: {str(inner_e)}")
                    db.session.rollback()
                    raise inner_e
            
        except Exception as e:
            print(f"Outer error: {str(e)}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        flash('If an account exists with this email, you will receive reset instructions.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    user = User.query.filter_by(reset_token=token).first()
    
    if user is None or (user.reset_token_expiration and 
            user.reset_token_expiration < datetime.utcnow()):
        flash('Invalid or expired reset token. Please try again.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not is_valid_password(password):
            flash('Password must be at least 8 characters long and contain uppercase, lowercase, and numbers', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
            
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiration = None
        db.session.commit()
        
        flash('Your password has been reset successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.email = request.form.get('email', current_user.email).strip().lower()
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating profile.', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
    return render_template('auth/edit_profile.html')