import os
import sys
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Message, Appointment

def run_test_flow():
    print("\n" + "="*50)
    print("🚀 TESTING JESICA FLOW: END-TO-END")
    print("="*50)
    
    test_phone = "whatsapp:+123456789"
    
    with app.app_context():
        # Clean up test user
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            Message.query.filter_by(user_id=user.id).delete()
            Appointment.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
            print("Cleanup: Deleted existing test user.")

        with app.test_client() as client:
            # STEP 1: Discovery
            print("\n🔵 STEP 1: Discovery (Asking about services)")
            res = client.post('/webhook/', data={'Body': 'Hola, ¿qué servicios ofrecen?', 'From': test_phone})
            print(f"Agent: {res.data.decode()}")

            # STEP 2: Intent to book
            print("\n🔵 STEP 2: Intent to book (Ordering Minilipo)")
            res = client.post('/webhook/', data={'Body': 'Quiero agendar para una minilipo', 'From': test_phone})
            print(f"Agent: {res.data.decode()}")

            # STEP 3: Provide Info (Including Phone)
            print("\n🔵 STEP 3: Provide Info (Name, Cedula, Email, Phone)")
            # Simulating all info in one go
            res = client.post('/webhook/', data={
                'Body': 'Mi nombre es Juan Pérez, mi cédula es 0999999999, mi correo es juan@example.com y mi celular es 0987654321', 
                'From': test_phone
            })
            print(f"Agent: {res.data.decode()}")
            
            # Verify DB state
            user = User.query.filter_by(phone_number=test_phone).first()
            print(f"DEBUG DB: Name={user.name}, Cedula={user.cedula}, Email={user.email}, Step={user.current_flow_step}")
            if user.current_flow_step == 'provide_slots':
                print("✅ Internal State correctly moved to 'provide_slots'.")
            else:
                print(f"❌ Internal State MISMATCH: Expected 'provide_slots', got '{user.current_flow_step}'")

            # STEP 4: Test Business Hours (Out of window)
            # Wednesday 7 PM (outside 8am-6pm)
            # Find next Wednesday
            now = datetime.now()
            days_ahead = 2 - now.weekday() # Wednesday is 2
            if days_ahead <= 0: days_ahead += 7
            next_wednesday = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
            print(f"\n🔵 STEP 4: Requesting out-of-hours slot ({next_wednesday} 19:00)")
            res = client.post('/webhook/', data={'Body': f'Quiero ir el miércoles {next_wednesday} a las 7 pm', 'From': test_phone})
            resp_text = res.data.decode()
            print(f"Agent: {resp_text}")
            if "8:00 AM a 6:00 PM" in resp_text:
                print("✅ Correctly rejected invalid weekday slot.")
            else:
                print("❌ Failed to reject weekday slot OR wrong hours mentioned.")

            # STEP 5: Test Business Hours (Saturday In window)
            # Saturday 11 AM (inside 8am-1:30pm)
            days_ahead = 5 - now.weekday() # Saturday is 5
            if days_ahead <= 0: days_ahead += 7
            next_saturday = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
            print(f"\n🔵 STEP 5: Requesting valid Saturday slot ({next_saturday} 11:00 AM)")
            res = client.post('/webhook/', data={'Body': f'Agendemos entonces el sábado {next_saturday} a las 11 am', 'From': test_phone})
            resp_text = res.data.decode()
            print(f"Agent: {resp_text}")
            
            # Verify internal booking
            from sqlalchemy import text
            db.session.expire_all()
            current_user = User.query.filter_by(phone_number=test_phone).first()
            
            # Raw SQL check
            raw_appts = db.session.execute(text("SELECT * FROM appointments")).fetchall()
            print(f"DEBUG DB: Raw SQL Total appointments: {len(raw_appts)}")
            for ra in raw_appts:
                print(f"DEBUG DB: Raw SQL Appt ID={ra[0]}, UserID={ra[1]}, Start={ra[2]}")
            
            all_appts = Appointment.query.all()
            print(f"DEBUG DB: SQLAlchemy Total appointments: {len(all_appts)}")
            
            appt = Appointment.query.filter_by(user_id=current_user.id).first()
            if appt and current_user.current_flow_step == 'waiting_for_payment':
                print(f"✅ Booking successful. Internal state: {current_user.current_flow_step}")
                print(f"✅ Appointment found: {appt.start_time}")
            else:
                print(f"❌ Booking failed. Appt found: {appt is not None}, Step: {current_user.current_flow_step}, UserID: {current_user.id}")
                # Check messages too
                msgs = Message.query.filter_by(user_id=current_user.id).all()
                print(f"DEBUG DB: Total messages for user: {len(msgs)}")

            # STEP 6: Verify Placeholders and Bank Details
            print("\n🔵 STEP 6: Verify Bank Details and Deposit Value ($30)")
            if "$30" in resp_text and "Banco Pichincha" in resp_text:
                print("✅ Placeholder [DEPOSIT_VALUE] and [BANK_DETAILS] resolved correctly.")
            else:
                print("❌ Placeholders or bank details missing.")

    print("\n" + "="*50)
    print("🏁 TEST COMPLETE")
    print("="*50)

if __name__ == "__main__":
    run_test_flow()
