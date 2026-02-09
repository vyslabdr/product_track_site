from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='staff') # admin, staff
    last_login = db.Column(db.DateTime, nullable=True)
    is_first_login = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    devices = db.relationship('Device', backref='customer', lazy=True)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(20), unique=True, nullable=False)
    
    # Customer Relationship
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    model = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=True) # Added Brand
    description = db.Column(db.Text, nullable=True)
    technician_notes = db.Column(db.Text, nullable=True) # Added Tech Notes
    status = db.Column(db.String(50), default='Παραλήφθηκε') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Ownership & Assignment
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    technician_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='devices_created')
    technician = db.relationship('User', foreign_keys=[technician_id], backref='devices_assigned')
    
    logs = db.relationship('TimelineLog', backref='device', lazy=True, cascade="all, delete-orphan")

class TimelineLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text, nullable=True) # Keeping for backward compatibility or general logging
    public_note = db.Column(db.Text, nullable=True) # Added Public Note
    private_note = db.Column(db.Text, nullable=True) # Added Private Note
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Who did this?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref='logs')

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Active Channel Selection
    active_channel = db.Column(db.String(20), default='sms') # sms, whatsapp, viber

    # SMS Configuration
    infobip_api_key_sms = db.Column(db.String(200), nullable=True)
    infobip_base_url_sms = db.Column(db.String(200), nullable=True)
    infobip_sender_id_sms = db.Column(db.String(50), default='InfoSMS')

    # WhatsApp Configuration
    infobip_api_key_wa = db.Column(db.String(200), nullable=True)
    infobip_base_url_wa = db.Column(db.String(200), nullable=True)
    infobip_number_wa = db.Column(db.String(50), nullable=True)

    # Viber Configuration
    infobip_api_key_viber = db.Column(db.String(200), nullable=True)
    infobip_base_url_viber = db.Column(db.String(200), nullable=True)
    infobip_sender_viber = db.Column(db.String(50), nullable=True)
    
    # Message Templates (Greek)
    # Message Templates (Greek)
    template_registration = db.Column(db.Text, default='Η συσκευή {model} με κωδικό {tracking_id} παρελήφθη. Ευχαριστούμε!')
    template_ready = db.Column(db.Text, default='Η συσκευή σας {model} ({tracking_id}) είναι έτοιμη για παραλαβή!')
    template_delivered = db.Column(db.Text, default='H συσκευή {model} παραδόθηκε. Ευχαριστούμε που μας προτιμήσατε!')

class NotificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    channel = db.Column(db.String(20), nullable=False) # SMS, WHATSAPP
    status = db.Column(db.String(20), nullable=False) # SENT, FAILED
    message_content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    device_rel = db.relationship('Device', backref='notifications')
