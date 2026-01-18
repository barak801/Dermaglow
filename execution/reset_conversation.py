import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Message, Appointment

def reset_user(phone_number):
    with app.app_context():
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            print(f"User with phone {phone_number} not found.")
            return

        # Delete messages
        Message.query.filter_by(user_id=user.id).delete()
        
        # Delete appointments (optional, but good for a fresh start)
        Appointment.query.filter_by(user_id=user.id).delete()
        
        # Reset identity and flow state
        user.name = None
        user.email = None
        user.cedula = None
        user.treatment_interest = None
        user.current_flow_step = 'welcome'
        
        db.session.commit()
        print(f"Successfully reset conversation for {phone_number}. State set to 'welcome'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 execution/reset_conversation.py <phone_number>")
        print("Example: python3 execution/reset_conversation.py whatsapp:+123456789")
    else:
        phone = sys.argv[1]
        reset_user(phone)
