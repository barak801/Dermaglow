import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("MIGRATION: Adding 'summary' column to 'users' table...")
        try:
            db.session.execute(text("ALTER TABLE users ADD COLUMN summary TEXT;"))
            db.session.commit()
            print("Successfully added 'summary' column.")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("'summary' column already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
