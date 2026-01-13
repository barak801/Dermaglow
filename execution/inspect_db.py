import sqlite3
import os

def inspect_db(db_path="dermaglow.db"):
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("The database is empty (no tables found).")
            return

        for table in tables:
            table_name = table[0]
            print(f"\n--- Table: {table_name} ---")
            
            # Get table content
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(" | ".join(columns))
            print("-" * (len(" | ".join(columns)) + 4))
            
            for row in rows:
                print(" | ".join(str(val) for val in row))

        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    inspect_db()
