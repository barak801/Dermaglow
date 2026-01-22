import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Message, Appointment

def reset_user(phone):
    # Twilio format usually includes 'whatsapp:' prefix
    whatsapp_phone = f"whatsapp:{phone}"
    
    with app.app_context():
        user = User.query.filter((User.phone_number == phone) | (User.phone_number == whatsapp_phone)).first()
        if not user:
            print(f"❌ User with phone {phone} not found.")
            return

        print(f"🔄 Resetting user: {user.phone_number} (ID: {user.id})")
        
        # Delete related data
        msg_count = Message.query.filter_by(user_id=user.id).delete()
        appt_count = Appointment.query.filter_by(user_id=user.id).delete()
        
        # Reset user state
        user.current_flow_step = 'welcome'
        user.name = None
        user.email = None
        user.cedula = None
        user.treatment_interest = None
        user.temp_system_hint = None
        user.summary = None
        
        db.session.commit()
        print(f"✅ Deleted {msg_count} messages and {appt_count} appointments.")
        print(f"✅ User state reset to 'welcome'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 reset_user.py <phone_number>")
    else:
        target_phone = sys.argv[1]
        reset_user(target_phone)
