import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User, Message, Appointment

def reset_all():
    with app.app_context():
        print("Starting full system reset (User data)...")
        
        # Deleting in order of dependencies
        try:
            num_appointments = Appointment.query.delete()
            print(f"Deleted {num_appointments} appointments.")
            
            num_messages = Message.query.delete()
            print(f"Deleted {num_messages} messages.")
            
            num_users = User.query.delete()
            print(f"Deleted {num_users} users.")
            
            db.session.commit()
            print("Successfully reset all user-related data.")
        except Exception as e:
            db.session.rollback()
            print(f"Error during reset: {e}")

if __name__ == "__main__":
    reset_all()
