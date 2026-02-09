import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('repair_shop_v7.db')
        cursor = conn.cursor()
        
        tables = ['customer', 'device', 'timeline_log']
        with open('schema_info.txt', 'w') as f:
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                f.write(f"--- {table} ---\n")
                for col in columns:
                    f.write(f"{col[1]} ({col[2]})\n")
                f.write("\n")
        
        conn.close()
        print("Schema info written to schema_info.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
