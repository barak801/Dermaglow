import os, requests
from requests.auth import HTTPBasicAuth
import json
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def calculate_next_business_slot(start_time, hours_delay):
    """
    Add hours_delay to start_time.
    If the result is after COMM_END_HOUR, move it to COMM_START_HOUR the next day.
    If the result is before COMM_START_HOUR, move it to COMM_START_HOUR today.
    """
    comm_start = int(os.getenv('COMM_START_HOUR', 10))
    comm_end = int(os.getenv('COMM_END_HOUR', 22))
    
    target_time = start_time + timedelta(hours=hours_delay)
    
    if target_time.hour < comm_start:
        target_time = target_time.replace(hour=comm_start, minute=0, second=0, microsecond=0)
    elif target_time.hour >= comm_end:
        target_time = (target_time + timedelta(days=1)).replace(hour=comm_start, minute=0, second=0, microsecond=0)
    
    return target_time

def get_calendar_service():
    scopes = ['https://www.googleapis.com/auth/calendar']
    if os.path.exists('service_account.json'):
        # Using service account JSON as requested by the user.
        try:
            creds = service_account.Credentials.from_service_account_file('service_account.json', scopes=scopes)
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"Error loading Calendar credentials: {e}")
    return None

def check_calendar_conflict(service, start_time, duration_mins=60):
    if not service: return False
    
    # Load timezone from env or default to Bogota (-5)
    tz_str = os.getenv('TIMEZONE', 'America/Bogota')
    local_tz = pytz.timezone(tz_str)
    
    # Ensure start_time is localized
    if start_time.tzinfo is None:
        start_time = local_tz.localize(start_time)
        
    end_time = start_time + timedelta(minutes=duration_mins)
    
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_time.isoformat(),
        timeMax=end_time.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return len(events) > 0

def book_google_event(service, start_time, user_name, duration_mins=60):
    if not service: return "PLACEHOLDER_ID"
    
    tz_str = os.getenv('TIMEZONE', 'America/Bogota')
    local_tz = pytz.timezone(tz_str)
    
    if start_time.tzinfo is None:
        start_time = local_tz.localize(start_time)
        
    end_time = start_time + timedelta(minutes=duration_mins)
    event = {
        'summary': f'Cita: {user_name}',
        'start': {'dateTime': start_time.isoformat(), 'timeZone': tz_str},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': tz_str},
    }
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    event = service.events().insert(calendarId=calendar_id, body=event).execute()
    event_id = event.get('id')
    print(f"DEBUG: Booked Google Calendar event. ID: {event_id}")
    return event_id

def get_available_slots(service, start_date=None, num_slots=2):
    """
    Finds the next available business slots starting from start_date.
    Returns a list of datetime objects (localized).
    """
    if not service: return []
    
    tz_str = os.getenv('TIMEZONE', 'America/Bogota')
    local_tz = pytz.timezone(tz_str)
    
    if not start_date:
        start_date = datetime.now(local_tz)
    
    if start_date.tzinfo is None:
        start_date = local_tz.localize(start_date)

    comm_start = int(os.getenv('COMM_START_HOUR', 10))
    comm_end = int(os.getenv('COMM_END_HOUR', 22))
    
    slots = []
    current_search_time = start_date
    
    # Simple search: check hour by hour during business hours
    # Limit to searching 7 days ahead
    max_search_days = 7
    search_limit = start_date + timedelta(days=max_search_days)
    
    while len(slots) < num_slots and current_search_time < search_limit:
        # 1. Skip Sundays
        if current_search_time.weekday() == 6: # Sunday
            current_search_time = (current_search_time + timedelta(days=1)).replace(hour=comm_start, minute=0)
            continue

        # 2. Handle Saturday (9am - 2pm based on flow.json)
        is_saturday = current_search_time.weekday() == 5
        sat_start = 9
        sat_end = 14
        
        effective_start = sat_start if is_saturday else comm_start
        effective_end = sat_end if is_saturday else comm_end

        # Ensure we are within business hours
        if current_search_time.hour < effective_start:
            current_search_time = current_search_time.replace(hour=effective_start, minute=0, second=0, microsecond=0)
        elif current_search_time.hour >= effective_end:
            # Skip to next day's comm_start
            current_search_time = (current_search_time + timedelta(days=1)).replace(hour=comm_start, minute=0, second=0, microsecond=0)
            continue # Re-evaluate day/skip sunday
            
        # Check if this slot is free
        if not check_calendar_conflict(service, current_search_time):
            # Only add if it's in the future
            if current_search_time > datetime.now(local_tz) + timedelta(minutes=30):
                slots.append(current_search_time)
        
        current_search_time += timedelta(hours=1)
        
    return slots

def delete_google_event(service, event_id):
    if not service or not event_id or event_id == "PLACEHOLDER_ID":
        return
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"Deleted Google Calendar event: {event_id}")
    except Exception as e:
        print(f"Error deleting event: {e}")

def get_sheets_service():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    if os.path.exists('service_account.json'):
        try:
            creds = service_account.Credentials.from_service_account_file('service_account.json', scopes=scopes)
            return build('sheets', 'v4', credentials=creds)
        except Exception as e:
            print(f"Error loading Sheets credentials: {e}")
    return None

def sync_appointment_to_sheet(appt_data):
    """
    Appends a new appointment or updates an existing one in Google Sheets.
    appt_data: dict with date, time, name, phone, status, google_event_id, notes
    """
    spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
    if not spreadsheet_id:
        print("GOOGLE_SHEET_ID not set in .env")
        return

    service = get_sheets_service()
    if not service: return

    # Detect the name of the first sheet tab dynamically.
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    sheet_name = sheets[0].get('properties', {}).get('title', 'Sheet1') if sheets else 'Sheet1'
    sheet_id = sheets[0].get('properties', {}).get('sheetId', 0) if sheets else 0
    
    range_name = f'{sheet_name}!A:G' # Date, Time, Name, Phone, Status, EventID, Notes
    
    # Check if appointment already exists (by Event ID)
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    rows = result.get('values', [])
    
    row_to_update = None
    headers = ["Date", "Time", "Name", "Phone", "Client Notes", "Status", "Event ID"]
    
    # Check if sheet is empty and initialize headers
    if not rows or len(rows) == 0:
        print(f"Sheet '{sheet_name}' is empty. Initializing headers...")
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=f'{sheet_name}!A1:G1',
            valueInputOption='RAW', body={'values': [headers]}
        ).execute()
        
        # Format headers (Bold, Centered, Grey Background)
        fmt_body = {
            "requests": [{
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 7},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                            "textFormat": {"bold": True},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            }]
        }
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=fmt_body).execute()
        # Re-fetch rows after header insertion
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        rows = result.get('values', [])

    for i, row in enumerate(rows):
        if len(row) > 6 and row[6] == appt_data['google_event_id']:
            row_to_update = i + 1 # 1-indexed
            break

    values = [[
        appt_data['date'],
        appt_data['time'],
        appt_data['name'],
        appt_data['phone'],
        appt_data.get('notes', ''),
        appt_data['status'],
        appt_data['google_event_id']
    ]]
    
    # Define colors
    color_map = {
        'PAID/CONFIRMED': {'red': 0.8, 'green': 1.0, 'blue': 0.8}, # Light Green
        'CANCELLED': {'red': 1.0, 'green': 0.8, 'blue': 0.8},      # Light Red
        'PENDING_PAYMENT': {'red': 1.0, 'green': 1.0, 'blue': 0.8} # Light Yellow
    }
    
    status_color = color_map.get(appt_data['status'], {'red': 1.0, 'green': 1.0, 'blue': 1.0})

    try:
        if row_to_update:
            # Update existing row
            update_range = f'{sheet_name}!A{row_to_update}:G{row_to_update}'
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=update_range,
                valueInputOption='RAW', body={'values': values}
            ).execute()
            print(f"Updated sheet row {row_to_update} for event {appt_data['google_event_id']} in '{sheet_name}'")
            target_row_index = row_to_update - 1
        else:
            # Append new row
            append_res = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption='RAW', body={'values': values}
            ).execute()
            print(f"Appended new appointment to '{sheet_name}'")
            # Get the index of the newly appended row
            updated_range = append_res.get('updates', {}).get('updatedRange', '')
            # e.g. Sheet1!A10:G10
            # Be robust: find the last occurrence of '!A' or just split by '!A'
            target_row_index = int(updated_range.split('!A')[-1].split(':')[0]) - 1

        # Apply formatting (background color)
        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": target_row_index,
                            "endRowIndex": target_row_index + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 7
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": status_color
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        
    except Exception as e:
        print(f"Error syncing to Google Sheets: {e}")

def get_client_summary(user_id):
    """
    Generates a concise summary of client history using Gemini.
    """
    from models import db, Message
    
    # Fetch last 20 messages for context
    msgs = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp.desc()).limit(20).all()
    if not msgs:
        return "No previous history."
    
    history_text = "\n".join([f"{m.role}: {m.content}" for m in reversed(msgs)])
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    Based on the following conversation history, write a 1-sentence summary (in SPANISH) of the client's interests, 
    concerns, or previous treatments. Be extremely concise.
    
    History:
    {history_text}
    
    Summary:
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating client summary: {e}")
        return "History summary unavailable."

def get_gemini_rag_response(user_input, system_instruction=None, context_files=[], history=[]):
    """
    Generates a response using Gemini, attaching files for true RAG.
    system_instruction provides the persona and context.
    context_files should be a list of 'gemini_name' identifiers.
    history should be a list of dicts: [{'role': 'user', 'parts': [...]}, {'role': 'model', 'parts': [...]}]
    """
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        system_instruction=system_instruction
    )
    
    # We use chat session to maintain history context properly
    chat = model.start_chat(history=history)
    
    # Fetch file references from Gemini
    message_parts = []
    
    if context_files:
        print(f"--- ATTACHING KB FILES: {context_files} ---")
        for g_name in context_files:
            try:
                # Retrieve the file handle from Gemini Cloud
                g_file = genai.get_file(g_name)
                message_parts.append(g_file)
            except Exception as e:
                print(f"Error fetching Gemini file {g_name}: {e}")

    # Add the current user input
    message_parts.append(user_input)

    try:
        # Send message with attached files
        response = chat.send_message(message_parts)
        return response.text.strip()
    except Exception as e:
        print(f"Error in Gemini RAG response: {e}")
        return "I'm sorry, I'm having trouble accessing my knowledge base right now."

def verify_payment_screenshot(media_url, expected_amount):
    """
    Downloads a screenshot from Twilio and uses Gemini Vision to verify the payment.
    expected_amount should be a string like '$30'.
    """
    try:
        # 1. Download the image
        # Twilio Media URLs usually require Basic Auth for private media
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        response = requests.get(media_url, auth=HTTPBasicAuth(account_sid, auth_token))
        if response.status_code != 200:
            print(f"Failed to download image from {media_url}. Status: {response.status_code}")
            return {'valid': False, 'reason': f"Download failed ({response.status_code})"}
        content = response.content
        
        # 2. Save to temp file
        tmp_dir = os.path.join(os.getcwd(), '.tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_filename = f"payment_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        tmp_path = os.path.join(tmp_dir, tmp_filename)
        
        with open(tmp_path, 'wb') as f:
            f.write(content)
        
        # 3. Analyze with Gemini Vision
        print(f"Analyzing payment screenshot: {tmp_path} for {expected_amount}")
        sample_file = genai.upload_file(path=tmp_path, display_name="Payment Proof")
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        Analyze this screenshot to verify a deposit payment for a medical aesthetic clinic.
        Target Amount: {expected_amount}
        
        Tasks:
        1. Identify if this is a payment receipt/confirmation (Transferencia, Nequi, Daviplata, or Bank receipt).
        2. Extract the TOTAL AMOUNT paid.
        3. Check if the amount matches {expected_amount}.
        
        Return ONLY a JSON object:
        {{
          "is_receipt": bool,
          "amount_matches": bool,
          "amount_found": "string value found",
          "currency": "string currency",
          "reason": "brief explanation"
        }}
        """
        
        result = model.generate_content([sample_file, prompt])
        res_text = result.text.strip()
        
        if res_text.startswith('```json'):
            res_text = res_text.split('```json')[1].split('```')[0].strip()
        elif res_text.startswith('```'):
            res_text = res_text.split('```')[1].split('```')[0].strip()
            
        return json.loads(res_text)
        
    except Exception as e:
        print(f"Error in payment verification: {e}")
        return {'valid': False, 'reason': str(e)}
