import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Message
import json

def test_full_flow():
    print("--- TESTING VIP FLOW 2.0 ---")
    
    with app.app_context():
        # Clean up or use a test phone
        test_phone = "whatsapp:+123456789"
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            from models import Message, Appointment
            Message.query.filter_by(user_id=user.id).delete()
            Appointment.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
        
        # 1. GREETING
        print("\nStep 1: Greeting")
        with app.test_client() as client:
            res = client.post('/webhook/', data={'Body': 'Hola', 'From': test_phone})
            user = User.query.filter_by(phone_number=test_phone).first()
            print(f"AI Response Snippet: {res.data.decode()[:100]}...")
            print(f"Current State: {user.current_flow_step}")
        
        # 2. DISCOVERY (Interest in Implantes Mamarios - Should trigger surgery question)
        print("\nStep 2: Interest in Implantes Mamarios (Surgical)")
        with app.test_client() as client:
            res = client.post('/webhook/', data={'Body': 'Quisiera información sobre implantes mamarios', 'From': test_phone})
            user = User.query.filter_by(phone_number=test_phone).first()
            output = res.data.decode()
            print(f"AI Response: {output}")
            print(f"Current State: {user.current_flow_step}")
            
        # 3. AREA/DETAIL (Confirming interest)
        print("\nStep 3: Detail / No previous surgery")
        with app.test_client() as client:
            res = client.post('/webhook/', data={'Body': 'No, no he tenido cirugías antes.', 'From': test_phone})
            user = User.query.filter_by(phone_number=test_phone).first()
            output = res.data.decode()
            print(f"AI Response Snippet: {output[:100]}...")
            print(f"Current State: {user.current_flow_step}")

        # 4. READY TO BOOK
        print("\nStep 4: Ready to Book")
        with app.test_client() as client:
            res = client.post('/webhook/', data={'Body': 'Si, me gustaría agendar una evaluación', 'From': test_phone})
            user = User.query.filter_by(phone_number=test_phone).first()
            output = res.data.decode()
            print(f"AI Response Snippet: {output[:100]}...")
            print(f"Current State: {user.current_flow_step}")
            
        # 5. PROVIDE INFO (Testing updated requirements: Name, Cédula, Email)
        print("\nStep 5: Providing Info (Name, ID, Email)")
        with app.test_client() as client:
            res = client.post('/webhook/', data={'Body': 'Mi nombre es Juan Pérez, mi cedula es 12345678 y mi correo jp@example.com', 'From': test_phone})
            user = User.query.filter_by(phone_number=test_phone).first()
            output = res.data.decode()
            print(f"AI Response Snippet: {output[:100]}...")
            print(f"Current State: {user.current_flow_step}")
            print(f"User Data: Name={user.name}, Email={user.email}, Cedula={user.cedula}")

if __name__ == "__main__":
    test_full_flow()
