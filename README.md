# Device Tracking System (Greek)

A locally hosted device tracking SaaS for repair shops.

## Features
- **Public Page**: 
  - Customer tracking via Device ID (SERxxxxxx).
  - **New:** Displays **Brand & Model** for better context.
  - **Clean Timeline:** Intelligence logic filters duplicate status updates.
  - **Glassmorphism UI:** Modern, translucent design.
  - **Lottie Animations**: Visual status updates for each repair stage.
- **Dashboard**:
  - **Stats**: Real-time overview cards with status filtering.
  - **Active Devices**: Manage repairs with color-coded status badges.
  - **Archive**: Searchable history of completed and delivered devices.
  - **Admin Panel**: Manage staff accounts and **System Settings**.
  - **Smart Logic**: Prevents duplicate notifications/timeline entries.
  - **SMS Integration**: Configure Infobip for automated status notifications.
- **Label Printing**: 58mm/80mm thermal printer compatible QR codes.
- **Workflow**: Defined lifecycle with Greek status updates:
  1. **Παραλήφθηκε** (Received)
  2. **Υπό Έλεγχο** (Checking)
  3. **Υπό Επισκευή** (Repairing)
  4. **Έτοιμο** (Ready)
  5. **Αρχείο** (Archived)

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

### 🔄 Factory Reset
To wipe the database and start fresh:
```bash
python3 reset_db.py
```
This will delete all data and recreate the `admin` user with the default password.

## Architecture
- **Backend**: Python (Flask) + SQLite
- **Frontend**: HTML5 + Vanilla JS + Tailwind CSS (CDN)
# product_track_site
