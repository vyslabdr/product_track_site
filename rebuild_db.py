import sys
print("Starting rebuild script...")
sys.stdout.flush()

try:
    from flask import Flask
    print("Flask imported")
    from flask_sqlalchemy import SQLAlchemy
    print("SQLAlchemy imported")
    from models import db
    print("models.db imported")
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///repair_shop_v7.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("Initializing DB...")
db.init_app(app)

with app.app_context():
    print("Creating all tables...")
    sys.stdout.flush()
    db.create_all()
    print("SUCCESS: Tables created.")
    sys.stdout.flush()
