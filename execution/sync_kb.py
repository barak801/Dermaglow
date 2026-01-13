import os
import sqlite3
import google.generativeai as genai
from dotenv import load_dotenv

# Load configuration
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

def sync_kb(file_path="qa.txt", db_path="dermaglow.db"):
    upload_path = os.path.join("uploads", file_path)
    if not os.path.exists(file_path):
        if os.path.exists(upload_path):
            file_path = upload_path
        else:
            print(f"Error: {file_path} not found in root or uploads/.")
            return

    print(f"Uploading {file_path} to Gemini...")
    try:
        # 1. Upload to Gemini
        file_ref = genai.upload_file(path=file_path, display_name="Clinic QA")
        print(f"Gemini File URI: {file_ref.name}")

        # 2. Update Database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if record exists
        cursor.execute("SELECT id FROM knowledge_base WHERE file_name = ?", (os.path.basename(file_path),))
        row = cursor.fetchone()
        
        if row:
            cursor.execute("UPDATE knowledge_base SET file_uri = ? WHERE id = ?", (file_ref.name, row[0]))
            print(f"Updated existing record (ID: {row[0]}) in {db_path}")
        else:
            cursor.execute("INSERT INTO knowledge_base (file_name, file_uri) VALUES (?, ?)", 
                           (os.path.basename(file_path), file_ref.name))
            print(f"Created new record in {db_path}")
        
        conn.commit()
        conn.close()
        print("Knowledge Base synced successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    sync_kb()
