import sqlite3

def migrate():
    conn = sqlite3.connect('repair_shop_v7.db')
    cursor = conn.cursor()
    
    try:
        # Add columns to Device table
        try:
            cursor.execute("ALTER TABLE device ADD COLUMN brand VARCHAR(100)")
            print("Added column: device.brand")
        except sqlite3.OperationalError:
            print("Column device.brand likely already exists.")
            
        try:
            cursor.execute("ALTER TABLE device ADD COLUMN technician_notes TEXT")
            print("Added column: device.technician_notes")
        except sqlite3.OperationalError:
             print("Column device.technician_notes likely already exists.")

        # Add columns to TimelineLog table
        try:
            cursor.execute("ALTER TABLE timeline_log ADD COLUMN public_note TEXT")
            print("Added column: timeline_log.public_note")
        except sqlite3.OperationalError:
             print("Column timeline_log.public_note likely already exists.")

        try:
            cursor.execute("ALTER TABLE timeline_log ADD COLUMN private_note TEXT")
            print("Added column: timeline_log.private_note")
        except sqlite3.OperationalError:
             print("Column timeline_log.private_note likely already exists.")
             
        conn.commit()
        print("Migration complete.")
        
    except Exception as e:
        with open('migration_log.txt', 'a') as f:
            f.write(f"Migration Error: {e}\n")
        print(f"Migration Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    with open('migration_log.txt', 'w') as f:
        f.write("Starting migration...\n")
    migrate()
