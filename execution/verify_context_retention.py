import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Message

def verify_context():
    print("--- VERIFYING CONTEXT RETENTION ---")
    
    test_phone = "whatsapp:+999999999"
    
    with app.app_context():
        # Ensure DB is ready
        db.create_all()
        
        # Clean up
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            from models import Appointment
            Message.query.filter_by(user_id=user.id).delete()
            Appointment.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
            
        with app.test_client() as client:
            # 1. Ask about a specific treatment
            print("\nStep 1: Ask about Minilipo")
            res1 = client.post('/webhook/', data={'Body': 'Hola, ¿qué es la minilipo?', 'From': test_phone})
            text1 = res1.data.decode()
            print(f"Agent Response 1: {text1}")
            
            # 2. Ask follow-up WITHOUT naming the treatment
            print("\nStep 2: Ask follow-up about price/duration")
            res2 = client.post('/webhook/', data={'Body': '¿Y cuánto cuesta? ¿duele?', 'From': test_phone})
            text2 = res2.data.decode()
            print(f"Agent Response 2: {text2}")
            
            # Check for context
            keywords = ['minilipo', 'precio', 'costo', 'valor', 'dólares', 'cirugía', 'grasa']
            found = [kw for kw in keywords if kw in text2.lower()]
            
            if found or "minilipo" in text2.lower():
                print("\n✅ SUCCESS: Agent seems to maintain context!")
                print(f"Found keywords: {found}")
            else:
                print("\n❌ FAILURE: Agent might have lost context.")
            
if __name__ == "__main__":
    verify_context()
