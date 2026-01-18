import os
import mimetypes
from app import app
from models import db, KnowledgeFile
from utils import genai

def sync_existing_files():
    upload_dir = 'uploads'
    if not os.path.exists(upload_dir):
        print("Uploads directory not found.")
        return

    with app.app_context():
        # Clean current DB to avoid duplicates during sync if necessary
        # KnowledgeFile.query.delete() 
        
        files = os.listdir(upload_dir)
        for filename in files:
            filepath = os.path.join(upload_dir, filename)
            if os.path.isfile(filepath):
                # Check if already in DB
                existing = KnowledgeFile.query.filter_by(filename=filename).first()
                if existing:
                    print(f"File {filename} already in database. Skipping.")
                    continue

                print(f"Syncing {filename} to Gemini...")
                try:
                    mime_type, _ = mimetypes.guess_type(filepath)
                    if not mime_type:
                        mime_type = 'text/plain'
                    
                    gemini_file = genai.upload_file(
                        path=filepath, 
                        display_name=filename,
                        mime_type=mime_type
                    )
                    
                    k_file = KnowledgeFile(
                        filename=filename, 
                        gemini_uri=gemini_file.uri,
                        gemini_name=gemini_file.name
                    )
                    db.session.add(k_file)
                    print(f"Successfully synced {filename} (Gemini ID: {gemini_file.name})")
                except Exception as e:
                    print(f"Error syncing {filename}: {e}")
        
        db.session.commit()
        print("Sync complete.")

if __name__ == "__main__":
    sync_existing_files()
