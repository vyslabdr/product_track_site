from app import app, db, Device, Customer, TimelineLog, generate_device_id
from datetime import datetime
from sqlalchemy import func

def create_test_data():
    with app.app_context():
        print("Creating test data for 4 main statuses (Greek)...")
        
        statuses = ['Παραλήφθηκε', 'Υπό Έλεγχο', 'Υπό Επισκευή', 'Έτοιμο']
        
        # Ensure a customer exists
        customer = Customer.query.first()
        if not customer:
            customer = Customer(name="Test Customer", phone="5551234567")
            db.session.add(customer)
            db.session.commit()

        # Admin User
        from app import User
        admin = User.query.filter_by(username='admin').first()
        admin_id = admin.id if admin else 1

        for status in statuses:
            new_id = generate_device_id()
            device = Device(
                tracking_id=new_id,
                customer_id=customer.id,
                model=f"Test Model - {status}",
                description=f"Auto-generated test for {status}",
                status=status,
                created_by_id=admin_id
            )
            db.session.add(device)
            # Add log
            log = TimelineLog(device=device, status=status, note=f"Initial status", user_id=admin_id)
            db.session.add(log)
            print(f"Created device {new_id} with status: {status}")
            
        db.session.commit()
        print("Done!")

if __name__ == "__main__":
    create_test_data()
