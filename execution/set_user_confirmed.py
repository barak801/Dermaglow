import sys
import os
# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db, User

def set_confirmed(phone):
    with app.app_context():
        user = User.query.filter_by(phone_number=phone).first()
        if not user:
            user = User(phone_number=phone)
            db.session.add(user)
        user.current_flow_step = 'collect_user_info'
        db.session.commit()
        print(f"User {phone} set to 'confirmed' state.")

if __name__ == "__main__":
    phone = sys.argv[1] if len(sys.argv) > 1 else "whatsapp:+1111111111"
    set_confirmed(phone)
