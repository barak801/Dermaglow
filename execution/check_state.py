import os, sys
sys.path.append(os.getcwd())
from app import app
from models import User

with app.app_context():
    u = User.query.filter_by(phone_number='whatsapp:+573161154777').first()
    if u:
        print(f"User: {u.phone_number}")
        print(f"State: {u.current_flow_step}")
    else:
        print("User not found.")
