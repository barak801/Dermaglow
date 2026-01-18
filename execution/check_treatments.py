import os
import sys

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from app import app, db
from models import Treatment

def check():
    with app.app_context():
        treatments = Treatment.query.all()
        print(f"Total treatments found: {len(treatments)}")
        for t in treatments:
            print(f"\n--- {t.name} ---")
            print(f"Category: {t.category}")
            print(f"Description: {t.description[:100]}...")
            print(f"Body Parts: {t.body_parts}")
            print(f"Benefits: {t.benefits.count(chr(10)) + 1} items listed")
            print(f"Duration: {t.duration}")
            print(f"Recovery: {t.recovery_time}")
            print(f"Price Info: {t.price_info}")

if __name__ == "__main__":
    check()
