# Device Tracking System (Greek)

A locally hosted device tracking SaaS for repair shops.

## Features
- **Public Page**: Customer tracking via Device ID.
- **Dashboard**:
  - **Stats**: Overview cards (Total, In Repair, Ready, Archived).
  - **Active Devices**: Manage current repairs.
  - **Archive**: Searchable history of delivered devices.
  - **Staff Management**: Admin-only panel to manage employees.
- **Label Printing**: 58mm/80mm thermal printer compatible QR codes.
- **Timeline**: Visual status updates.

## Setup & Run

1. **Install Dependencies** (if not already done):
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   ./venv/bin/python app.py
   ```
   *Note: On first run, `repair_shop.db` will be created automatically.*

3. **Access**:
   - **Public Page**: [http://localhost:5000](http://localhost:5000)
   - **Login**: [http://localhost:5000/login](http://localhost:5000/login)
   - **Dashboard**: [http://localhost:5000/dashboard](http://localhost:5000/dashboard)

## Default Credentials
- **Auto-Seeding**: The admin user is automatically created on first run.
- **User**: `admin`
- **Password**: `admin123`
- **First Login**: You will be required to change the password immediately.

## Architecture
- **Backend**: Python (Flask) + SQLite
- **Frontend**: HTML5 + Vanilla JS + Tailwind CSS (CDN)
# product_track_site
