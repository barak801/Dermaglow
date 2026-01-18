from app import app, db
from models import User, Message, Appointment
from utils import get_calendar_service, delete_google_event
from datetime import datetime, timedelta

def test_accuracy_edge_cases():
    print("--- TESTING ACCURACY EDGE CASES (MULTI-INTENT) ---")
    
    with app.app_context():
        test_phone = "whatsapp:+999888777"
        # Cleanup
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            appts = Appointment.query.filter_by(user_id=user.id).all()
            service = get_calendar_service()
            for a in appts:
                delete_google_event(service, a.google_event_id)
            Message.query.filter_by(user_id=user.id).delete()
            Appointment.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()

        client = app.test_client()

        # Step 1: Getting to Discovery
        client.post('/webhook/', data={'Body': 'Hola', 'From': test_phone})

        # Step 2: Multi-Intent (Question + Booking)
        # Should go to ask_booking_details, not stay in discovery questions
        print("\nTest: Question + Booking Intent")
        res = client.post('/webhook/', data={'Body': '¿Cuanto cuesta el tratamiento? Quisiera agendar para mañana.', 'From': test_phone})
        # If successful, it should ask for preferring date/time and mention deposit (ask_booking_details state)
        response_body = res.data.decode()
        print(f"User: ¿Cuanto cuesta el tratamiento? Quisiera agendar para mañana.\nAI Response:\n{response_body}")
        
        if "depósito" in response_body.lower() or "30" in response_body:
            print("SUCCESS: Prioritized booking over question.")
        else:
            print("FAILURE: May have prioritized question over booking.")

        # Cleanup
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            appts = Appointment.query.filter_by(user_id=user.id).all()
            service = get_calendar_service()
            for a in appts:
                delete_google_event(service, a.google_event_id)

if __name__ == "__main__":
    test_accuracy_edge_cases()
