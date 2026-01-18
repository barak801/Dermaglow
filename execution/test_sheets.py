import os
from dotenv import load_dotenv
from utils import sync_appointment_to_sheet

load_dotenv()

def test_sheet_connection():
    print("--- TESTING GOOGLE SHEETS CONNECTIVITY ---")
    spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    if not spreadsheet_id:
        print("Error: GOOGLE_SHEET_ID is missing in .env")
        return

    test_data = {
        'date': '2026-01-15',
        'time': '00:00',
        'name': 'TEST COLORS',
        'phone': 'whatsapp:+999999999',
        'status': 'PAID/CONFIRMED',
        'google_event_id': 'test_colors_id_456',
        'notes': 'This row should be light GREEN to verify visual tracking.'
    }
    
    print(f"Attempting to write to Sheet: {spreadsheet_id}")
    try:
        sync_appointment_to_sheet(test_data)
        print("\nSUCCESS: Check your spreadsheet for a 'TEST CONNECTION' row!")
    except Exception as e:
        print(f"\nFAILURE: Could not connect to Google Sheets: {e}")

if __name__ == "__main__":
    test_sheet_connection()
