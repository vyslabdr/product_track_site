import sqlite3
import os

print(f"CWD: {os.getcwd()}")
try:
    conn = sqlite3.connect('repair_shop_v7.db', timeout=10)
    cursor = conn.cursor()
    
    sqls = [
        "ALTER TABLE device ADD COLUMN brand VARCHAR(100)",
        "ALTER TABLE device ADD COLUMN technician_notes TEXT",
        "ALTER TABLE timeline_log ADD COLUMN public_note TEXT",
        "ALTER TABLE timeline_log ADD COLUMN private_note TEXT"
    ]
    
    for sql in sqls:
        try:
            cursor.execute(sql)
            print(f"Executed: {sql}")
        except Exception as e:
            print(f"Error executing {sql}: {e}")
            
    conn.commit()
    conn.close()
    print("Done.")
except Exception as e:
    print(f"Connection Error: {e}")
