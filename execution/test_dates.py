import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Message, Appointment

def test_relative_date_flow():
    print("--- TESTING RELATIVE DATE EXTRACTION ---")
    
    with app.app_context():
        test_phone = "whatsapp:+987654321"
        test_phone_en = "whatsapp:+111222333"
        for p in [test_phone, test_phone_en]:
            user = User.query.filter_by(phone_number=p).first()
            if user:
                Message.query.filter_by(user_id=user.id).delete()
                Appointment.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()
        
        # 1. State: discovery (move to ask_booking_details)
        print("\nStep 1: Set state to discovery and ask for booking")
        with app.test_client() as client:
            future_date_text = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            res = client.post('/webhook/', data={'Body': f'Quiero agendar para el {future_date_text} a las 12pm', 'From': test_phone})
            print(f"AI Response (ES):\n{res.data.decode()}")
            user = User.query.filter_by(phone_number=test_phone).first()
            print(f"Current State: {user.current_flow_step}")
            
            appt = Appointment.query.filter_by(user_id=user.id).first()
            if appt:
                expected_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                print(f"Booked Date: {appt.start_time.strftime('%Y-%m-%d %H:%M')}")
                if appt.start_time.strftime("%Y-%m-%d") == expected_date:
                    print("SUCCESS: 'Mañana' correctly extracted!")
                else:
                    print(f"FAILURE: Expected {expected_date}, got {appt.start_time.strftime('%Y-%m-%d')}")
            else:
                print("FAILURE: No appointment created.")

        # 2. Test English "tomorrow"
        print("\nStep 2: Test English 'tomorrow'")
        test_phone_en = "whatsapp:+111222333"
        with app.test_client() as client:
            client.post('/webhook/', data={'Body': 'Hi, I want a minilipo. How much is it?', 'From': test_phone_en})
            res = client.post('/webhook/', data={'Body': 'Ok, book me for tomorrow at 6:17pm', 'From': test_phone_en})
            print(f"AI Response (EN):\n{res.data.decode()}")
            
            user_en = User.query.filter_by(phone_number=test_phone_en).first()
            appt_en = Appointment.query.filter_by(user_id=user_en.id).filter(Appointment.start_time >= datetime.now()).first()
            if appt_en:
                print(f"Booked Date (EN): {appt_en.start_time.strftime('%Y-%m-%d %H:%M')}")
                expected_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                if appt_en.start_time.strftime("%Y-%m-%d") == expected_date:
                    print("SUCCESS: 'Tomorrow' correctly extracted!")
                else:
                    print(f"FAILURE: Expected {expected_date}, got {appt_en.start_time.strftime('%Y-%m-%d')}")
            else:
                print("FAILURE: No appointment created for EN.")

if __name__ == "__main__":
    test_relative_date_flow()
