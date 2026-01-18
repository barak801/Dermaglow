from utils import get_calendar_service
import json

def diagnose():
    service = get_calendar_service()
    if not service:
        print("❌ Could not load calendar service.")
        return

    try:
        print("--- Listing Calendars ---")
        calendar_list = service.calendarList().list().execute()
        items = calendar_list.get('items', [])
        if not items:
            print("No extra calendars found. Only 'primary' (service account's own).")
        else:
            for calendar in items:
                print(f"ID: {calendar['id']}")
                print(f"Summary: {calendar['summary']}")
                print(f"Primary: {calendar.get('primary', False)}")
                print("-" * 20)
                
        # Also try to print the service account email if possible
        if hasattr(service, '_http'):
            # This is a bit hacky, but let's see if we can find the email in credentials
            pass
            
    except Exception as e:
        print(f"Error listing calendars: {e}")

if __name__ == "__main__":
    diagnose()
