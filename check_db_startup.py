import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from app import app, db, User, Device
    print("Imports successful.")
    
    with app.app_context():
        # Check DB Connection
        db.engine.connect()
        print("Database connection successful.")
        
        # Check Tables
        users = User.query.count()
        print(f"Users table check: {users} users found.")
        
        # Check Admin exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user verified.")
        else:
            print("WARNING: Admin user missing.")
            
    print("SUCCESS: Database startup check passed.")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
