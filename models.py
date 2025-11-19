from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import pytz

db = SQLAlchemy()

def get_indonesia_time():
    """Get current Indonesia time (WIB)"""
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(jakarta_tz)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    wallet_balance = db.Column(db.Float, default=0)
    role = db.Column(db.String(10), default="user")
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=get_indonesia_time)
    
    payments = db.relationship('Payment', backref='user', lazy=True)
    accesses = db.relationship('Access', backref='user', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('email', 'is_deleted', name='unique_email_not_deleted'),
    )

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=get_indonesia_time)
    
    videos = db.relationship('Video', backref='category', lazy=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    embed_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    price = db.Column(db.Float, default=0)
    is_premium = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=get_indonesia_time)
    
    # TAMBAHKAN FIELD BARU UNTUK CLOUDINARY UPLOAD
    video_url = db.Column(db.String(1024))  # URL video dari Cloudinary
    public_id = db.Column(db.String(512))   # Public ID dari Cloudinary
    video_type = db.Column(db.String(20), default='embed')  # 'embed' atau 'upload'
    
    accesses = db.relationship('Access', backref='video', lazy=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")
    payment_method = db.Column(db.String(50))
    proof_url = db.Column(db.String(500))
    sender_name = db.Column(db.String(100))
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_indonesia_time)
    updated_at = db.Column(db.DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)

class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: get_indonesia_time() + timedelta(hours=48))
    created_at = db.Column(db.DateTime, default=get_indonesia_time)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    text_color = db.Column(db.String(20), default="#ffffff")
    text_style = db.Column(db.String(50), default="normal")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_indonesia_time)
    updated_at = db.Column(db.DateTime, default=get_indonesia_time, onupdate=get_indonesia_time)