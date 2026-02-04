
import unittest
import json
from app import app, db, User, Device, Customer, SystemSetting
from werkzeug.security import generate_password_hash

class ProductTrackTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for API tests
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Create Admin
            admin = User(username='admin', password_hash=generate_password_hash('admin'), role='admin')
            db.session.add(admin)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_auth(self):
        rv = self.login('admin', 'admin')
        self.assertIn(b'logout', rv.data.lower()) # Should see logout link
        
    def test_add_device_new_customer(self):
        self.login('admin', 'admin')
        response = self.app.post('/add_device', data={
            'customer_name': 'Test Customer',
            'phone': '5551234567',
            'model': 'iPhone 13',
            'description': 'Broken Screen'
        }, follow_redirects=True)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        with app.app_context():
            # Verify Customer Created
            cust = Customer.query.filter_by(phone='5551234567').first()
            self.assertIsNotNone(cust)
            self.assertEqual(cust.name, 'Test Customer')
            
            # Verify Device Created
            dev = Device.query.filter_by(tracking_id=data['id']).first()
            self.assertIsNotNone(dev)
            self.assertEqual(dev.customer_id, cust.id)
            self.assertEqual(dev.status, 'Σε Εκκρεμότητα')

    def test_add_device_existing_customer(self):
        self.login('admin', 'admin')
        # Create customer first
        with app.app_context():
            cust = Customer(name='Old Name', phone='5559999999')
            db.session.add(cust)
            db.session.commit()
            
        # Add device with SAME phone but NEW name
        response = self.app.post('/add_device', data={
            'customer_name': 'New Name', # Should update name
            'phone': '5559999999',
            'model': 'Samsung S21',
            'description': 'Battery'
        })
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        with app.app_context():
            cust = Customer.query.filter_by(phone='5559999999').first()
            self.assertEqual(cust.name, 'New Name') # Name updated?
            self.assertEqual(len(cust.devices), 1)

    def test_settings_api(self):
        self.login('admin', 'admin')
        # GET empty settings
        rv = self.app.get('/api/settings')
        data = rv.json
        self.assertIsNone(data['api_key'])
        
        # POST settings
        settings_data = {
            'api_key': 'TEST_KEY',
            'base_url': 'api.infobip.com',
            'sender_id': 'TEST_SENDER',
            'channels_reg': 'sms,whatsapp'
        }
        rv = self.app.post('/api/settings', json=settings_data)
        self.assertTrue(rv.json['success'])
        
        with app.app_context():
            s = SystemSetting.query.first()
            self.assertEqual(s.infobip_api_key, 'TEST_KEY')
            self.assertEqual(s.channels_registration, 'sms,whatsapp')

if __name__ == '__main__':
    unittest.main()
