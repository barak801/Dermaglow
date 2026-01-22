import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, extract_entities, handle_attempt_booking, db, User
import pytz
from datetime import datetime

with app.app_context():
    user = User.query.filter_by(phone_number='whatsapp:+573161154777').first()
    if not user:
        print("User not found")
        exit()
    
    # Pre-populate user data for sheet sync
    user.name = "Barak Test"
    user.email = "barak@test.com"
    user.cedula = "1234567890"
    user.treatment_interest = "Lipo MicroAire"
    db.session.commit()
    
    local_tz = pytz.timezone('America/Bogota')
    now_local = datetime.now(local_tz)
    
    data = {
        'preferred_day': '2026-01-30',
        'preferred_hour': '10:00',
    }
    
    print(f"\n--- Testing 9-Column Booking Sync ---")
    hints, next_step = handle_attempt_booking(user, data, local_tz, now_local)
    print(f"Hints: {hints}")
    print(f"Next Step: {next_step}")
