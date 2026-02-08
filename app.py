import io
import requests
import qrcode
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Device, TimelineLog, SystemSetting, NotificationLog, Customer

import os
import logging

# Configure Logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'repair_shop_v7.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def init_db():
    """Ensure database tables exist on startup."""
    with app.app_context():
        try:
            db.create_all()
            # Check for Admin
            if not User.query.filter_by(username='admin').first():
                 logging.info("Auto-creating admin user...")
                 # Generate hash for 'admin123'
                 # We need to import generate_password_hash here or ensure it is available
                 from werkzeug.security import generate_password_hash
                 admin = User(username='admin', password_hash=generate_password_hash('admin123'), role='admin')
                 db.session.add(admin)
                 db.session.commit()
                 logging.info("Admin user created (admin/admin123).")
        except Exception as e:
            logging.error(f"Database Initialization Error: {e}")

# Initialize DB on import (or run manually)
init_db()

# --- Helpers ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

import random
import string

def generate_device_id():
    """Generates a unique SER-ID (e.g., SER7A2B9)."""
    prefix = "SER"
    
    while True:
        # Generate 6 random characters (uppercase letters + digits)
        chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        new_id = f"{prefix}{chars}"
        
        # Check uniqueness against DB
        if not Device.query.filter_by(tracking_id=new_id).first():
            return new_id

# --- Routes: Auth ---
@app.before_request
def check_first_login():
    if current_user.is_authenticated and getattr(current_user, 'is_first_login', False):
        if request.endpoint not in ['change_password', 'logout', 'static']:
            flash('Ειδοποίηση Ασφαλείας: Πρέπει να αλλάξετε τον κωδικό σας στην πρώτη σύνδεση.', 'warning')
            return redirect(url_for('change_password'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            
            # Check immediately after login
            if getattr(user, 'is_first_login', False):
                flash('Ειδοποίηση: Πρώτη σύνδεση. Παρακαλούμε αλλάξτε τον κωδικό σας.', 'warning')
                return redirect(url_for('change_password'))
                
            return redirect(url_for('dashboard'))
        flash('Λανθασμένο όνομα χρήστη ή κωδικός πρόσβασης', 'error')
    return render_template('login.html')

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('Όλα τα πεδία είναι υποχρεωτικά.', 'error')
            return render_template('change_password.html')
            
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Ο τρέχων κωδικός είναι λάθος.', 'error')
            return render_template('change_password.html')

        if len(new_password) < 8:
            flash('Ο νέος κωδικός πρέπει να είναι τουλάχιστον 8 χαρακτήρες.', 'error')
            return render_template('change_password.html')
            
        if new_password != confirm_password:
            flash('Οι κωδικοί δεν ταιριάζουν.', 'error')
            return render_template('change_password.html')
            
        # Update Password
        current_user.password_hash = generate_password_hash(new_password)
        current_user.is_first_login = False
        db.session.commit()
        
        flash('Ο κωδικός ενημερώθηκε επιτυχώς.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('change_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# @app.route('/create_admin')
# def create_admin():
#     # Helper to create initial admin - DISABLED FOR SECURITY
#     # Run via flask shell if needed:
#     # from app import db, User
#     # from werkzeug.security import generate_password_hash
#     # db.session.add(User(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
#     # db.session.commit()
#     return "Route disabled. Use CLI."

# --- Routes: Public ---
@app.route('/')
def index():
    return render_template('index.html')

import json

# from infobip_service import InfobipService

# --- SETTINGS ROUTES ---
@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def manage_settings():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        settings = SystemSetting.query.first()
        if not settings:
            settings = SystemSetting()
            db.session.add(settings)
            db.session.commit()
    except Exception as e:
        logging.error(f"Database Error loading settings: {e}")
        # If table missing, we can try to create? Or just return default structure for now to prevent crash
        # For this specific user request: "return default empty values or create table"
        # We'll return a mock settings object or empty dict structure if query fails hard
        return jsonify({'error': 'Database not initialized or Settings table missing', 'details': str(e)}), 500

    if request.method == 'POST':
        data = request.json
        
        # General
        settings.active_channel = data.get('active_channel', 'sms')
        
        # SMS
        settings.infobip_api_key_sms = data.get('api_key_sms')
        settings.infobip_base_url_sms = data.get('base_url_sms')
        settings.infobip_sender_id_sms = data.get('sender_id_sms')
        
        # WhatsApp
        settings.infobip_api_key_wa = data.get('api_key_wa')
        settings.infobip_base_url_wa = data.get('base_url_wa')
        settings.infobip_number_wa = data.get('number_wa')
        
        # Viber
        settings.infobip_api_key_viber = data.get('api_key_viber')
        settings.infobip_base_url_viber = data.get('base_url_viber')
        settings.infobip_sender_viber = data.get('sender_viber')

        # Templates
        settings.template_registration = data.get('template_reg')
        settings.template_ready = data.get('template_ready')
        settings.template_delivered = data.get('template_del')
        
        db.session.commit()
        return jsonify({'success': True})
        
    return jsonify({
        'active_channel': settings.active_channel,
        
        'api_key_sms': settings.infobip_api_key_sms,
        'base_url_sms': settings.infobip_base_url_sms,
        'sender_id_sms': settings.infobip_sender_id_sms,
        
        'api_key_wa': settings.infobip_api_key_wa,
        'base_url_wa': settings.infobip_base_url_wa,
        'number_wa': settings.infobip_number_wa,
        
        'api_key_viber': settings.infobip_api_key_viber,
        'base_url_viber': settings.infobip_base_url_viber,
        'sender_viber': settings.infobip_sender_viber,

        'template_reg': settings.template_registration,
        'template_ready': settings.template_ready,
        'template_del': settings.template_delivered
    })


@app.route('/track')
def track_device():
    tracking_id = request.args.get('id')
    if not tracking_id:
        return jsonify({'error': 'Missing ID'}), 400
        
    device = Device.query.filter_by(tracking_id=tracking_id).first()
    if not device:
        return jsonify({'error': 'Not found'}), 404
        
    timeline = []
    for log in device.logs:
        staff_name = log.user.username if log.user else 'System'
        timeline.append({
            'status': log.status,
            'note': log.note,
            'date': log.timestamp.strftime('%d/%m/%Y %H:%M'), # Changed from log.timestamp to log.created_at to match model
            'staff': staff_name
        })
    
    # Notification History for Timeline (Optional visibility? Requirement said "Device Details". This is public track.)
    # Let's keep public track minimal.
        
    return jsonify({
        'device': {
            'model': device.model,
            'status': device.status,
            'timeline': timeline
        }
    })

@app.route('/api/devices/<int:device_id>/notifications')
@login_required
def get_device_notifications(device_id):
    device = Device.query.get_or_404(device_id)
    logs = [{
        'channel': n.channel,
        'status': n.status,
        'message': n.message_content,
        'timestamp': n.timestamp.strftime('%d/%m/%Y %H:%M')
    } for n in device.notifications]
    return jsonify(logs)

# --- Routes: Dashboard ---
@app.route('/dashboard')
@login_required
def dashboard():
    # Initial load still passes active devices for SEO/Non-JS fallback if needed, but client prefers AJAX.
    # We will pass basic context and let JS fetch specific tabs.
    return render_template('dashboard.html', user=current_user)

@app.route('/api/devices')
@login_required
def get_devices():
    status_filter = request.args.get('status')
    user_id = request.args.get('user_id')
    
    query = Device.query
    
    # User Filter (Ownership or Technician)
    if user_id:
        # Show devices created by OR assigned to this user
        # Also could filter logged actions, but visual ownership usually means "My Tasks" (Technician) or "My Entries"
        user = User.query.get(user_id)
        if user:
            # Complex filter: (technician_id == uid) OR (created_by_id == uid)
            query = query.filter((Device.technician_id == user_id) | (Device.created_by_id == user_id))

    # Status Filter - Greek Terms
    # Παραλήφθηκε (Yellow), Υπό Έλεγχο (Blue), Υπό Επισκευή (Orange), Έτοιμο (Green), Αρχείο (Gray)
    if status_filter == 'archive':
        query = query.filter_by(is_archived=True)
    elif status_filter == 'ready':
        query = query.filter_by(status='Έτοιμο', is_archived=False)
    elif status_filter == 'repair':
        query = query.filter_by(status='Υπό Επισκευή', is_archived=False)
    elif status_filter == 'checking':
        query = query.filter_by(status='Υπό Έλεγχο', is_archived=False)
    elif status_filter == 'received':
        query = query.filter_by(status='Παραλήφθηκε', is_archived=False)
    elif status_filter == 'active': 
        query = query.filter_by(is_archived=False)
        
    devices = query.order_by(Device.created_at.desc()).all()
    
    return jsonify([{
        'id': d.id,
        'tracking_id': d.tracking_id,
        'customer_name': d.customer.name,
        'phone': d.customer.phone,
        'model': d.model,
        'description': d.description,
        'status': d.status,
        'created_at': d.created_at.strftime('%d/%m/%Y'),
        'technician': d.technician.username if d.technician else '-',
        'created_by': d.created_by.username if d.created_by else '-'
    } for d in devices])

@app.route('/api/stats')
@login_required
def get_stats():
    user_id = request.args.get('user_id')
    base_query = Device.query
    
    if user_id:
        base_query = base_query.filter((Device.technician_id == user_id) | (Device.created_by_id == user_id))
    
    def count_with_filter(status_list, archived=False):
        q = base_query
        if archived:
            q = q.filter(Device.is_archived==True)
        else:
            q = q.filter(Device.is_archived==False)
            if status_list:
                q = q.filter(Device.status.in_(status_list))
        return q.count()

    # 6-Card System (Greek)
    total = count_with_filter(None, archived=False) # Σύνολο
    received = count_with_filter(['Παραλήφθηκε'], archived=False) # Yellow
    checking = count_with_filter(['Υπό Έλεγχο'], archived=False) # Blue
    repair = count_with_filter(['Υπό Επισκευή'], archived=False) # Orange
    ready = count_with_filter(['Έτοιμο'], archived=False) # Green
    completed = count_with_filter(None, archived=True) # Αρχείο
    
    return jsonify({
        'total': total,
        'received': received,
        'checking': checking,
        'repair': repair,
        'ready': ready,
        'completed': completed
    })

@app.route('/add_device', methods=['POST'])
@login_required
def add_device():
    try:
        data = request.form
        customer_name = data.get('customer_name')
        phone = data.get('phone')
        
        if not customer_name or not phone:
             return jsonify({'success': False, 'error': 'Name and Phone required'}), 400

        # customer_name might be existing customer? Logic: Check by phone
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            customer = Customer(name=customer_name, phone=phone)
            db.session.add(customer)
            db.session.commit() # Commit to get ID
        else:
            # Optional: Update name if changed?
            if customer.name != customer_name:
                customer.name = customer_name
                db.session.commit()

        new_id = generate_device_id()
        
        # Default status: Παραλήφθηκε
        device = Device(
            tracking_id=new_id,
            customer_id=customer.id,
            model=data.get('model'),
            description=data.get('description'),
            status='Παραλήφθηκε',
            created_by_id=current_user.id
        )
        db.session.add(device)
        
        # Initial log
        log = TimelineLog(device=device, status='Παραλήφθηκε', note='Device registered', user_id=current_user.id)
        db.session.add(log)
        db.session.commit()


        
        # Return token/id and also Who created it (for label)
        return jsonify({
            'success': True, 
            'id': new_id, 
            'created_by': current_user.username
        })
    except Exception as e:
        logging.error(f"Error adding device: {e}")
        return jsonify({'success': False, 'error': 'Server Error'}), 500

@app.route('/update_status/<int:device_id>', methods=['POST'])
@login_required
def update_status(device_id):
    device = Device.query.get_or_404(device_id)
    try:
        new_status = request.form.get('status')
        note = request.form.get('note', '')
        
        old_status = device.status
        device.status = new_status
        
        # If moving to "In Repair" (Στην επισκευή), assign current user as technician if not set?
        # User: "Τεχνικός: (İşlemi kim yapıyor?)"
        if new_status == 'Υπό Επισκευή' and not device.technician_id:
            device.technician_id = current_user.id

        if new_status == 'Αρχείο':
            device.is_archived = True
        else:
            device.is_archived = False # Allow un-archiving
            
        log = TimelineLog(device=device, status=new_status, note=note, user_id=current_user.id)
        db.session.add(log)
        db.session.commit()
        
        # TRIGGER NOTIFICATION via INFOBIP SERVICE
        if new_status == 'Έτοιμο':
            try:
                from infobip_service import InfobipService
                success, msg = InfobipService.send_notification(device, 'ready')
                if success:
                    logging.info(f"Notification Sent [ID:{device.tracking_id}]: {msg}")
                else:
                    logging.error(f"Notification Failed [ID:{device.tracking_id}]: {msg}")
            except Exception as e:
                 logging.error(f"Notification System Error: {e}")
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error updating status for device {device_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database Error'}), 500

@app.route('/generate_qr/<device_id>')
def generate_qr_code(device_id):
    device = Device.query.filter_by(tracking_id=device_id).first_or_404()
    # URL to the public tracking page
    url = url_for('index', _external=True) + f"?id={device.tracking_id}"
    
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# --- Staff Management ---
@app.route('/api/staff', methods=['GET', 'POST'])
@login_required
def manage_staff():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    if request.method == 'GET':
        staff_list = User.query.all()
        return jsonify([{
            'id': u.id,
            'username': u.username,
            'role': u.role,
            'last_login': u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else '-'
        } for u in staff_list])
    
    # POST - Add Staff
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'staff')

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'User exists'}), 400
        
    hashed = generate_password_hash(password)
    new_staff = User(username=username, password_hash=hashed, role=role)
    db.session.add(new_staff)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/staff/<int:user_id>', methods=['DELETE'])
@login_required
def delete_staff(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.username == 'admin': # Prevent deleting main admin
        return jsonify({'success': False, 'message': 'Cannot delete main admin'}), 400
        
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error deleting staff: {e}")
        return jsonify({'success': False, 'message': 'Database error'}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False) # use_reloader=False to prevent double init in some envs
