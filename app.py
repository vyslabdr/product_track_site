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
                 from werkzeug.security import generate_password_hash
                 admin = User(
                     username='admin', 
                     password_hash=generate_password_hash('admin123'), 
                     role='admin',
                     is_first_login=True # Force password change
                 )
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


# --- Routes: Public ---
@app.route('/')
def index():
    return render_template('index.html')

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
    last_status = None
    
    # Process logs in chronological order first
    for log in device.logs: # Relationship is usually ordered by timestamp desc in model? Check.
        # Logic: If status is same as previous, SKIP unless important note?
        # User requested: "Don't show same status twice".
        # We need to handle this carefully. If sorting is DESC (newest first), we iterate backwards or check next?
        # Device.logs is likely backref default (Lazy). Let's sort manually to be sure.
        pass

    # Sort logs NEWEST FIRST for display
    sorted_logs = sorted(device.logs, key=lambda x: x.timestamp, reverse=True)
    
    processed_timeline = []
    
    # We iterate and only add if status != next_status (since it's reverse order)
    # Actually, simpler: Show Newest status. 
    # If the next log (older) has same status, hide it? 
    # USER REQUEST: "admin presses 'Checking' twice -> timeline shouldn't show 'Checking' twice".
    # So we should filter out adjacent duplicates.
    
    for i, log in enumerate(sorted_logs):
        # Check against the NEXT log (which is the newer one in time if we were iterating asc, but here we are desc)
        # Wait, if we have [Status A, Status A, Status B], we want to show the LATEST Status A, and hide the older Status A?
        # Or show the Older Status A (when it started) and hide the newer "update" if it's just a note?
        # Usually "Timeline" shows when things happened.
        # User said: "Admin presses checking 2nd time, don't show it twice".
        # So if we have:
        # 12:00 Checking (Log 1)
        # 12:05 Checking (Log 2)
        # We likely want to show 12:05 Checking (Latest update). 
        # But if 12:05 was just a note "Still checking", we might want to show that note under "Checking".
        # Let's simple de-dup: If log[i].status == log[i+1].status, merge?
        
        # Simple Approach: Iterate and skip if status is same as *previous processed*? 
        # No, because we want to keep the LATEST one usually.
        
        # Let's filter:
        # Keep log if: It's the first one OR status != previous_kept_log.status?
        # If we list Newest -> Oldest:
        # Log 1 (New, Checking) -> Keep
        # Log 2 (Old, Checking) -> Skip? 
        # If we skip Log 2, we lose the info of when "Checking" *started*?
        # Maybe user wants to see the *Start* of the status?
        # "Admin presses checking TWICE".
        # 1. Status -> Checking. 
        # 2. Update -> Checking.
        # Result: "Checking" appears twice.
        # User wants it ONCE.
        # Ideally we show the *Latest* one? Or the *First* one?
        # Let's show the LATEST one (top of timeline) if they match.
        
        should_show = True
        if i < len(sorted_logs) - 1:
            next_log = sorted_logs[i+1] # This is OLDER
            if log.status == next_log.status:
                # This log and older log have same status. 
                # We are currently at the NEWER log.
                # If we show this, and then later show the older one, we have duplicates.
                # We should HIDE the OLDER one.
                # But we are iterating i... so we decide for 'next_log' later?
                # No, let's decide for CURRENT log.
                # If i > 0 (there is a NEWER log above me), and newer_log.status == my.status -> Hide ME.
                pass
        
    # Better logic: Filter list first.
    # We want to represent distinct *Phase Changes*.
    
    clean_timeline = []
    seen_statuses = set() 
    # But wait, status can go A -> B -> A. We shouldn't hide the second A group.
    # We only hide consecutive duplicates.
    
    # Iterate standard chronological (Old -> New) to build clean list
    chronological = sorted(device.logs, key=lambda x: x.timestamp)
    non_duplicate_logs = []
    
    last_added_status = None
    for log in chronological:
        if log.status != last_added_status:
            non_duplicate_logs.append(log)
            last_added_status = log.status
        else:
            # Same status. Update the last added log to be this one? 
            # Or just ignore this one?
            # If we ignore this one, we show the timestamp of the *START* of the status.
            # If we replace, we show timestamp of *LATEST* update.
            # Usually users want to know "When did it update?". 
            # If I add a note, I want to see the note.
            # Proposed: If same status, but has Public Note, show it as an "Update" item?
            # User request: "Ayni durumlar iki kez gosterilmemeli" => "Same statuses shouldn't be shown twice".
            # Let's strictly de-dup by Status.
            # If we have A -> A' -> B. We show A... then B. what about A'?
            # If A' has a note, we might lose it. 
            # Let's just update the "Latest" pointer for that status block?
            # Let's stick to: Hide consecutive duplicates.
            # If I stick to strict "Hide matches", I keep the FIRST one (Start time).
            pass
            
            # If there is a public note, we might want to keep it?
            if log.public_note:
                 non_duplicate_logs.append(log) # Keep it if it has a note.
    
    # Reverse for display (Newest top)
    final_logs = sorted(non_duplicate_logs, key=lambda x: x.timestamp, reverse=True)
    
    for log in final_logs:
        staff_name = log.user.username if log.user else 'System'
        timeline.append({
            'status': log.status,
            'note': log.public_note or log.note, # Show public note
            'date': log.timestamp.strftime('%d/%m/%Y %H:%M'),
            'staff': staff_name
        })

    return jsonify({
        'device': {
            'model': device.model,
            'brand': device.brand,
            'status': device.status,
            'description': device.description,
            'timeline': timeline
        }
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

@app.route('/api/devices/<int:device_id>/details')
@login_required
def get_device_details(device_id):
    device = Device.query.get_or_404(device_id)
    
    logs = []
    for log in device.logs:
        logs.append({
            'status': log.status,
            'public_note': log.public_note or log.note,
            'private_note': log.private_note,
            'timestamp': log.timestamp.strftime('%d/%m/%Y %H:%M'),
            'user': log.user.username if log.user else 'System'
        })
    # Sort logs desc
    logs.reverse()

    return jsonify({
        'id': device.id,
        'tracking_id': device.tracking_id,
        'brand': device.brand,
        'model': device.model,
        'status': device.status,
        'description': device.description,
        'technician_notes': device.technician_notes,
        'customer': {
            'name': device.customer.name,
            'phone': device.customer.phone,
            'email': device.customer.email
        },
        'logs': logs
    })

@app.route('/api/devices/<int:device_id>/update_notes', methods=['POST'])
@login_required
def update_technician_notes(device_id):
    try:
        device = Device.query.get_or_404(device_id)
        notes = request.json.get('technician_notes')
        device.technician_notes = notes
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
        'created_by': d.created_by.username if d.created_by else '-',
        'brand': d.brand or ''  # Added brand
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
        email = data.get('email') # Added email
        brand = data.get('brand') # Added brand
        
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
            if email: # Update email if provided
                 customer.email = email
            db.session.commit()

        new_id = generate_device_id()
        
        # Default status: Παραλήφθηκε
        device = Device(
            tracking_id=new_id,
            customer_id=customer.id,
            brand=brand, # Added brand
            model=data.get('model'),
            description=data.get('description'),
            status='Παραλήφθηκε',
            created_by_id=current_user.id
        )
        db.session.add(device)
        
        # Initial log
        log = TimelineLog(
            device=device, 
            status='Παραλήφθηκε', 
            public_note='Device registered', 
            private_note='', 
            note='Device registered', # Backward compat
            user_id=current_user.id
        )
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
        # Dual Notes
        public_note = request.form.get('public_note', '')
        private_note = request.form.get('private_note', '')
        
        old_status = device.status
        status_changed = (old_status != new_status)
        
        # If moving to "In Repair" (Στην επισκευή), assign current user as technician if not set?
        if new_status == 'Υπό Επισκευή' and not device.technician_id:
            device.technician_id = current_user.id

        if new_status == 'Αρχείο':
            device.is_archived = True
        else:
            device.is_archived = False 
            
        device.status = new_status 
        
        # Save log entry
        log = TimelineLog(
            device=device, 
            status=new_status, 
            public_note=public_note, 
            private_note=private_note,
            note=public_note, # Fallback
            user_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        # Smart Notification Logic: Only send if status CHANGED
        if status_changed:
            try:
                # Placeholder for Infobip integration
                # from infobip_service import InfobipService
                # InfobipService.send_status_update(device, new_status)
                pass
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
