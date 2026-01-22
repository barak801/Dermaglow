import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_sheets_service

def read_sheet():
    spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
    if not spreadsheet_id:
        print("GOOGLE_SHEET_ID not set")
        return

    service = get_sheets_service()
    if not service:
        print("Could not get sheets service")
        return

    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    sheet_name = sheets[0].get('properties', {}).get('title', 'Sheet1') if sheets else 'Sheet1'
    
    range_name = f'{sheet_name}!A1:G10'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    rows = result.get('values', [])
    
    if not rows:
        print('No data found.')
        return

    print(f"--- Sheet: {sheet_name} ---")
    for i, row in enumerate(rows):
        print(f"Row {i}: {row}")

if __name__ == "__main__":
    read_sheet()
