import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import Treatment, KnowledgeFile, User

def view_data():
    with app.app_context():
        print("\n" + "="*50)
        print("👥 PATIENT SUMMARIES (CRM)")
        print("="*50)
        users = User.query.filter(User.summary.isnot(None)).all()
        if not users:
            print("No patient summaries found.")
        for u in users:
            print(f"👤 {u.name or u.phone_number}")
            print(f"   Summary: {u.summary}")
            print("-" * 30)

        print("\n" + "="*50)
        print("🏛️  CURRENT TREATMENTS IN DATABASE")
        print("="*50)
        treatments = Treatment.query.all()
        if not treatments:
            print("No treatments found in database.")
        for t in treatments:
            print(f"🔹 [{t.id}] {t.name}")
            print(f"   Description: {t.description}")
            print(f"   Price: {t.price_info}")
            print(f"   Recovery: {t.recovery_time}")
            print(f"   Body Parts: {t.body_parts}")
            print("-" * 30)

        print("\n" + "="*50)
        print("📄 LINKED KNOWLEDGE BASE FILES (Gemini)")
        print("="*50)
        kb_files = KnowledgeFile.query.all()
        if not kb_files:
            print("No knowledge base files linked.")
        for k in kb_files:
            print(f"📁 {k.filename}")
            print(f"   Gemini Name: {k.gemini_name}")
            print("-" * 30)
        print("\n")

if __name__ == "__main__":
    view_data()
