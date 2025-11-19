from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Video, Access
from datetime import datetime, timedelta
import pytz

video_bp = Blueprint('video', __name__)

def get_indonesia_time():
    """Get current Indonesia time (WIB)"""
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(jakarta_tz)

@video_bp.route('/video/<int:video_id>')
@login_required
def video_detail(video_id):
    video = Video.query.get_or_404(video_id)
    return render_template('video_detail.html', video=video)

@video_bp.route('/watch/<int:video_id>')
@login_required
def watch(video_id):
    video = Video.query.get_or_404(video_id)
    
    # Check if video is free
    if not video.is_premium:
        return render_template('watch.html', video=video)
    
    # Check existing access using Indonesia time
    current_time = get_indonesia_time().replace(tzinfo=None)
    access = Access.query.filter_by(
        user_id=current_user.id, 
        video_id=video.id
    ).first()
    
    if access and access.expires_at > current_time:
        return render_template('watch.html', video=video)
    else:
        # Check if user has enough balance
        if current_user.wallet_balance >= video.price:
            # Deduct balance and grant access using Indonesia time
            current_user.wallet_balance -= video.price
            new_access = Access(
                user_id=current_user.id,
                video_id=video.id,
                expires_at=get_indonesia_time() + timedelta(hours=48)  # 48 jam WIB
            )
            db.session.add(new_access)
            db.session.commit()
            
            flash(f'Akses video premium diberikan! Berlaku 48 jam.', 'success')
            return render_template('watch.html', video=video)
        else:
            return render_template('need_payment.html', video=video)

@video_bp.route('/api/check_access/<int:video_id>')
@login_required
def check_access(video_id):
    video = Video.query.get_or_404(video_id)
    
    if not video.is_premium:
        return jsonify({'has_access': True})
    
    # Check access using Indonesia time
    current_time = get_indonesia_time().replace(tzinfo=None)
    access = Access.query.filter_by(
        user_id=current_user.id, 
        video_id=video.id
    ).first()
    
    has_access = access and access.expires_at > current_time
    return jsonify({'has_access': has_access})