import sqlite3
import os

db_path = 'repair_shop_v7.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} does not exist.")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(system_setting)")
    columns = [col[1] for col in cursor.fetchall()]

    required_columns = ['active_channel', 'template_registration', 'template_ready', 'template_delivered']
    missing = [c for c in required_columns if c not in columns]

    if not missing:
        print("SUCCESS: All required columns found.", flush=True)
    else:
        print(f"FAILURE: Missing columns: {missing}", flush=True)
        exit(1)

except Exception as e:
    print(f"Exception: {e}", flush=True)
    exit(1)
