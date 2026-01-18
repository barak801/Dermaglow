import os
from app import app
from models import db, KnowledgeFile

with app.app_context():
    files = KnowledgeFile.query.all()
    if not files:
        print("No knowledge files found in database.")
    else:
        for f in files:
            print(f"ID: {f.id}, Filename: {f.filename}, Gemini Name: {f.gemini_name}")
