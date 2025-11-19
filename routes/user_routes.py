from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Access
from datetime import datetime
import pytz

user_bp = Blueprint('user', __name__)

def get_indonesia_time():
    """Get current Indonesia time (WIB)"""
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(jakarta_tz)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Login berhasil! Selamat datang {user.email}', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Email atau password salah!', 'danger')
    
    return render_template('login.html')

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if len(password) < 6:
            flash('Password harus minimal 6 karakter!', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Password tidak cocok!', 'danger')
            return render_template('register.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email sudah terdaftar!', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email, 
            password=hashed_password,
            wallet_balance=0  # Default balance
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('user.login'))
    
    return render_template('register.html')

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('index'))

@user_bp.route('/profile')
@login_required
def profile():
    # Get active accesses using Indonesia time
    current_time = get_indonesia_time().replace(tzinfo=None)
    active_accesses = Access.query.filter(
        Access.user_id == current_user.id,
        Access.expires_at > current_time
    ).join(Access.video).all()
    
    return render_template('profile.html', active_accesses=active_accesses)

@user_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    # For future profile updates (email, password, etc.)
    flash('Fitur update profile akan segera tersedia!', 'info')
    return redirect(url_for('user.profile'))