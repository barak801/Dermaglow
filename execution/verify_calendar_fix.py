import os
from dotenv import load_dotenv
from utils import get_calendar_service
from datetime import datetime, timedelta

load_dotenv()

def verify_final():
    service = get_calendar_service()
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
    print(f"Targeting Calendar ID: {calendar_id}")
    
    try:
        now = datetime.utcnow().isoformat() + 'Z'
        print(f"--- Fetching events from {calendar_id} ---")
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"Successfully connected! Found {len(events)} upcoming events.")
        print("✅ CALENDAR ACCESS CONFIRMED")
        return True
    except Exception as e:
        print(f"❌ FAILED to access calendar: {e}")
        return False

if __name__ == "__main__":
    verify_final()
