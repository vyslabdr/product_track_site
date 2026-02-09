# Device Tracking System (Greek)

A locally hosted device tracking SaaS for repair shops.

## Features
- **Public Page**: 
  - Customer tracking via Device ID (SERxxxxxx).
  - **New:** Displays **Brand & Model** ("Μοντέλο Συσκευής") for better context.
  - **Clean Timeline:** Smart filters prevent duplicate status updates from cluttering the view.
  - **Visuals:** Lottie Animations for each repair stage.
  - **Localization:** fully localized in Greek.
- **Dashboard**:
  - **Stats**: Real-time overview cards with status filtering.
  - **Active Devices**: Manage repairs with color-coded status badges.
  - **Smart Notifications**: Logic to prevent duplicate SMS/WhatsApp alerts if the status and notes haven't changed.
  - **Admin Panel**: Manage staff accounts and **System Settings**.
  - **Infobip Integration**: Configure SMS, WhatsApp, or Viber for automated status updates.
- **Core Improvements**:
  - **Centralized Management**: Database initialization and Admin creation are handled automatically by the main application.
  - **Security**: Forced password change on first login.
- **Workflow**: Defined lifecycle with Greek status updates:
  1. **Παραλήφθηκε** (Received)
  2. **Υπό Έλεγχο** (Checking)
  3. **Υπό Επισκευή** (Repairing)
  4. **Έτοιμο** (Ready)
  5. **Αρχείο** (Archived)

## Setup & Run

1. **Install Dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```
   *Note: On the first run, the database `repair_shop_v7.db` and the default `admin` user will be created automatically.*

3. **Access**:
   - **Public Page**: [http://localhost:5000](http://localhost:5000)
   - **Login**: [http://localhost:5000/login](http://localhost:5000/login)
   - **Dashboard**: [http://localhost:5000/dashboard](http://localhost:5000/dashboard)

## Default Credentials
- **Auto-Seeding**: The admin user is automatically created on first run.
- **User**: `admin`
- **Password**: `admin123`
- **First Login**: You will be required to change the password immediately.

## Factory Reset
To wipe the database and start fresh, simply delete the `repair_shop_v7.db` file and restart the application.

## Architecture
- **Backend**: Python (Flask) + SQLite
- **Frontend**: HTML5 + Vanilla JS + Bootstrap 5
