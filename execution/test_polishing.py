from app import app, db
from models import User, Message, Appointment
from utils import get_calendar_service, delete_google_event
from datetime import datetime, timedelta

def test_strict_spanish_flow():
    print("--- TESTING STRICT SPANISH & LUXURY PERSONA ---")
    
    with app.app_context():
        test_phone = "whatsapp:+777888999"
        # Cleanup
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            # Delete any existing appointments from Google Calendar first
            appts = Appointment.query.filter_by(user_id=user.id).all()
            service = get_calendar_service()
            for a in appts:
                delete_google_event(service, a.google_event_id)
                
            Message.query.filter_by(user_id=user.id).delete()
            Appointment.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()

        client = app.test_client()

        # 1. Test Welcome message (should be Spanish)
        print("\nStep 1: Welcome message check")
        res = client.post('/webhook/', data={'Body': 'Hello', 'From': test_phone}) # English probe
        print(f"User: Hello\nAI Response:\n{res.data.decode()}")

        # 2. Test Discovery -> Focus on Evaluation in Spanish
        print("\nStep 2: Ask about services in English")
        res = client.post('/webhook/', data={'Body': 'What is Endolifting?', 'From': test_phone})
        print(f"User: What is Endolifting?\nAI Response:\n{res.data.decode()}")
        
        # 3. Test Booking Confirmation (deterministic Spanish)
        print("\nStep 3: Attempt Booking in English")
        # Use a highly specific time to avoid accidental collision
        unique_date = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        res = client.post('/webhook/', data={'Body': f'Book me for {unique_date} at 6:41pm', 'From': test_phone})
        print(f"User: Book me for {unique_date} at 6:41pm\nAI Response:\n{res.data.decode()}")

        # Final Cleanup for Calendar
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            appts = Appointment.query.filter_by(user_id=user.id).all()
            service = get_calendar_service()
            for a in appts:
                delete_google_event(service, a.google_event_id)
                
if __name__ == "__main__":
    test_strict_spanish_flow()
