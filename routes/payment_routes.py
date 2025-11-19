from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from models import db, Payment
import os
from werkzeug.utils import secure_filename
from datetime import datetime

payment_bp = Blueprint('payment', __name__)

# Buat folder uploads jika belum ada
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@payment_bp.route('/wallet')
@login_required
def wallet():
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(
        Payment.created_at.desc()
    ).all()
    return render_template('wallet.html', payments=payments)

@payment_bp.route('/wallet/topup', methods=['POST'])
@login_required
def topup():
    amount = float(request.form.get('amount', 0))
    payment_method = request.form.get('payment_method')
    sender_name = request.form.get('sender_name', '').strip()
    
    # UBAH DI SINI: dari 10000 menjadi 5000
    if amount < 5000:
        flash('Minimum top up adalah Rp 5.000!', 'danger')
        return redirect(url_for('payment.wallet'))
    
    if not sender_name:
        flash('Nama pengirim harus diisi!', 'danger')
        return redirect(url_for('payment.wallet'))
    
    if not payment_method:
        flash('Pilih metode pembayaran!', 'danger')
        return redirect(url_for('payment.wallet'))
    
    # ... kode selanjutnya tetap sama
    
    # Handle file upload
    proof_file = request.files.get('proof_file')
    
    if not proof_file or proof_file.filename == '':
        flash('Bukti transfer harus diupload!', 'danger')
        return redirect(url_for('payment.wallet'))
    
    if not allowed_file(proof_file.filename):
        flash('Format file tidak didukung! Gunakan PNG, JPG, JPEG, GIF, PDF, atau WEBP.', 'danger')
        return redirect(url_for('payment.wallet'))
    
    # Save uploaded file
    filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{proof_file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    proof_file.save(file_path)
    
    # Create payment record
    new_payment = Payment(
        user_id=current_user.id,
        amount=amount,
        status='pending',
        payment_method=payment_method,
        proof_url=filename,  # Simpan nama file saja
        sender_name=sender_name
    )
    
    db.session.add(new_payment)
    db.session.commit()
    
    flash(f'Permintaan top up Rp {amount:,.0f} berhasil dikirim! Silakan transfer ke 082320781747 dan tunggu verifikasi admin.', 'success')
    return redirect(url_for('payment.wallet'))

@payment_bp.route('/payment/instructions')
@login_required
def payment_instructions():
    method = request.args.get('method', 'dana')
    amount = request.args.get('amount', 0)
    
    payment_info = {
        'dana': {
            'number': '082320781747',
            'name': 'STREAMFLIX OFFICIAL',
            'instructions': [
                'Transfer ke DANA: 082320781747',
                'A/N: STREAMFLIX OFFICIAL',
                f'Jumlah: Rp {float(amount):,.0f}',
                'Pesan: "Top up - {}"'.format(current_user.email),
                'Setelah transfer, upload bukti di form top up'
            ]
        },
        'ovo': {
            'number': '082320781747',
            'name': 'STREAMFLIX OFFICIAL', 
            'instructions': [
                'Transfer ke OVO: 082320781747',
                'A/N: STREAMFLIX OFFICIAL',
                f'Jumlah: Rp {float(amount):,.0f}',
                'Pesan: "Top up - {}"'.format(current_user.email),
                'Setelah transfer, upload bukti di form top up'
            ]
        },
        'gopay': {
            'number': '082320781747',
            'name': 'STREAMFLIX OFFICIAL',
            'instructions': [
                'Transfer ke GoPay: 082320781747', 
                'A/N: STREAMFLIX OFFICIAL',
                f'Jumlah: Rp {float(amount):,.0f}',
                'Pesan: "Top up - {}"'.format(current_user.email),
                'Setelah transfer, upload bukti di form top up'
            ]
        },
        'bank_transfer': {
            'number': '082320781747 (BCA)',
            'name': 'STREAMFLIX OFFICIAL',
            'instructions': [
                'Transfer Bank BCA: 082320781747',
                'A/N: STREAMFLIX OFFICIAL',
                f'Jumlah: Rp {float(amount):,.0f}',
                'Berita: "Top up - {}"'.format(current_user.email),
                'Setelah transfer, upload bukti di form top up'
            ]
        }
    }
    
    info = payment_info.get(method, payment_info['dana'])
    return jsonify(info)

@payment_bp.route('/view_proof/<filename>')
@login_required
def view_proof(filename):
    """Endpoint untuk user melihat bukti transfer mereka"""
    payment = Payment.query.filter_by(proof_url=filename, user_id=current_user.id).first()
    
    if not payment and current_user.role != 'admin':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('payment.wallet'))
    
    return send_from_directory(UPLOAD_FOLDER, filename)