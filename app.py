from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import Config
from models import db, User, Video, Payment, Access, Category, Announcement
from flask_login import LoginManager, current_user, login_required
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash
import pytz

# Import blueprints
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from routes.video_routes import video_bp
from routes.payment_routes import payment_bp

def get_indonesia_time():
    """Get current Indonesia time (WIB)"""
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(jakarta_tz)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(video_bp)
    app.register_blueprint(payment_bp)
    
    # Template filter for datetime comparison - FIXED
    @app.template_filter('is_future')
    def is_future(dt):
        if dt is None:
            return False
        try:
            # Convert both to naive for safe comparison
            now_naive = get_indonesia_time().replace(tzinfo=None)
            dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
            return dt_naive > now_naive
        except Exception as e:
            print(f"Error in is_future filter: {e}")
            return False
    
    # Template filter untuk konversi waktu ke Indonesia
    @app.template_filter('indonesia_time')
    def indonesia_time_filter(dt):
        if dt is None:
            return ""
        try:
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            if dt.tzinfo is None:
                # If naive datetime, assume it's UTC
                dt = pytz.utc.localize(dt)
            indonesia_time = dt.astimezone(jakarta_tz)
            return indonesia_time.strftime('%d/%m/%Y %H:%M') + ' WIB'
        except Exception as e:
            print(f"Error converting time: {e}")
            return dt.strftime('%d/%m/%Y %H:%M')
    
    # Template filter untuk format waktu Indonesia (pendek)
    @app.template_filter('indonesia_datetime')
    def indonesia_datetime_filter(dt):
        if dt is None:
            return ""
        try:
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            if dt.tzinfo is None:
                # If naive datetime, assume it's UTC
                dt = pytz.utc.localize(dt)
            indonesia_time = dt.astimezone(jakarta_tz)
            return indonesia_time.strftime('%d/%m %H:%M')
        except Exception as e:
            print(f"Error converting datetime: {e}")
            return dt.strftime('%d/%m %H:%M')
    
    # Template filter untuk menghitung sisa waktu dalam jam (Indonesia Time)
    @app.template_filter('hours_remaining')
    def hours_remaining_filter(expires_at):
        if expires_at is None:
            return 0
        
        try:
            now = get_indonesia_time()
            # Convert both to naive datetime for comparison
            expires_naive = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
            now_naive = now.replace(tzinfo=None) if now.tzinfo else now
            
            time_left = expires_naive - now_naive
            
            if time_left.total_seconds() <= 0:
                return 0
            
            hours_left = time_left.total_seconds() / 3600
            return round(hours_left, 1)
                
        except Exception as e:
            print(f"Error calculating hours remaining: {e}")
            return 0
    
    # Global context processor - FIXED
    @app.context_processor
    def inject_now():
        # Get active announcements
        active_announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
        return {
            'now': get_indonesia_time(),
            'announcements': active_announcements
        }
    
    # Root route - Homepage - FIXED
    @app.route('/')
    def index():
        from models import Video, Access, Category
        # Get all videos and separate by category
        all_videos = Video.query.order_by(Video.created_at.desc()).all()
        
        free_videos = [v for v in all_videos if not v.is_premium]
        premium_videos = [v for v in all_videos if v.is_premium]
        
        # Get all categories for filter
        categories = Category.query.order_by(Category.name).all()
        
        # Get user's active accesses if logged in - FIXED
        active_accesses = []
        if current_user.is_authenticated:
            # Use Indonesia time for comparison
            current_time = get_indonesia_time().replace(tzinfo=None)
            active_accesses = Access.query.filter(
                Access.user_id == current_user.id,
                Access.expires_at > current_time
            ).all()
        
        return render_template('index.html', 
                             free_videos=free_videos,
                             premium_videos=premium_videos,
                             active_accesses=active_accesses,
                             categories=categories)
   
    
    # Search functionality - FIXED
    @app.route('/search')
    def search():
        from models import Video, Access, Category
        
        query = request.args.get('q', '')
        
        if query:
            # Search in title and description
            all_videos = Video.query.filter(
                Video.title.ilike(f'%{query}%') | 
                Video.description.ilike(f'%{query}%')
            ).order_by(Video.created_at.desc()).all()
        else:
            # If no query, show all videos
            all_videos = Video.query.order_by(Video.created_at.desc()).all()
        
        # Separate into free and premium
        free_videos = [v for v in all_videos if not v.is_premium]
        premium_videos = [v for v in all_videos if v.is_premium]
        
        # Get all categories for filter
        categories = Category.query.order_by(Category.name).all()
        
        # Get user's active accesses if logged in - FIXED
        active_accesses = []
        if current_user.is_authenticated:
            # Use Indonesia time for comparison
            current_time = get_indonesia_time().replace(tzinfo=None)
            active_accesses = Access.query.filter(
                Access.user_id == current_user.id,
                Access.expires_at > current_time
            ).all()
        
        return render_template('index.html', 
                             free_videos=free_videos,
                             premium_videos=premium_videos,
                             active_accesses=active_accesses,
                             categories=categories,
                             search_query=query)
    
    # Initialize admin user and database
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        admin = User.query.filter_by(email='misterxyz597@gmail.com').first()
        if not admin:
            admin_user = User(
                email='misterxyz597@gmail.com',
                password=generate_password_hash('Ubg72yisQwlc'),
                role='admin',
                wallet_balance=0
            )
            db.session.add(admin_user)
            db.session.commit()
            print("=" * 50)
            print("ADMIN USER CREATED SUCCESSFULLY!")
            print("Email: misterxyz597@gmail.com")
            print("Password: Ubg72yisQwlc")
            print("=" * 50)
        
        # HAPUS: Bagian pembuatan sample announcement dihapus sepenuhnya
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # API routes for AJAX calls
    @app.route('/api/user/balance')
    @login_required
    def api_user_balance():
        return {'balance': current_user.wallet_balance}
    
    @app.route('/api/stats')
    @login_required
    def api_stats():
        if current_user.role != 'admin':
            return {'error': 'Unauthorized'}, 403
        
        total_users = User.query.count()
        total_videos = Video.query.count()
        total_premium = Video.query.filter_by(is_premium=True).count()
        total_categories = Category.query.count()
        total_announcements = Announcement.query.count()
        total_active_announcements = Announcement.query.filter_by(is_active=True).count()
        total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.status == 'completed'
        ).scalar() or 0
        
        return {
            'total_users': total_users,
            'total_videos': total_videos,
            'total_premium': total_premium,
            'total_categories': total_categories,
            'total_announcements': total_announcements,
            'total_active_announcements': total_active_announcements,
            'total_revenue': total_revenue
        }
    
    # API untuk mendapatkan pengumuman aktif
    @app.route('/api/active_announcements')
    def api_active_announcements():
        announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.created_at.desc()).all()
        
        announcements_data = []
        for announcement in announcements:
            # Convert to Indonesia time
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            created_at_indonesia = announcement.created_at.astimezone(jakarta_tz) if announcement.created_at.tzinfo else pytz.utc.localize(announcement.created_at).astimezone(jakarta_tz)
            updated_at_indonesia = announcement.updated_at.astimezone(jakarta_tz) if announcement.updated_at.tzinfo else pytz.utc.localize(announcement.updated_at).astimezone(jakarta_tz)
            
            announcements_data.append({
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'created_at': created_at_indonesia.strftime('%d/%m/%Y %H:%M'),
                'updated_at': updated_at_indonesia.strftime('%d/%m/%Y %H:%M')
            })
        
        return jsonify(announcements_data)
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("🚀 StreamFlix starting...")
    print("📧 Admin Login: misterxyz597@gmail.com")
    print("🔑 Admin Password: Ubg72yisQwlc")
    print("🌐 Server running at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)