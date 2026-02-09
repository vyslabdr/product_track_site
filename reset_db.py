import os
from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_database():
    print("WARNING: This will delete all data in 'repair_shop_v7.db'.")
    confirm = input("Are you sure? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        return

    db_file = os.path.join(os.path.dirname(__file__), 'repair_shop_v7.db')
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Deleted {db_file}")

    with app.app_context():
        # Create Tables
        db.create_all()
        print("Database tables created.")

        # Create Admin with Force Change Password = True
        hashed_pw = generate_password_hash('admin123')
        admin = User(
            username='admin', 
            password_hash=hashed_pw, 
            role='admin',
            is_first_login=True  # FORCE CHANGE PASSWORD
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")
        print("Username: admin")
        print("Password: admin123")
        print("Force Change: ENABLED")

if __name__ == "__main__":
    reset_database()
