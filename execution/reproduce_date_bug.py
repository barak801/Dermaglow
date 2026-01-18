from datetime import datetime
import os
import pytz
from dotenv import load_dotenv
from utils import genai

load_dotenv()

def test_extraction():
    # Set context to Friday Jan 16, 2026 (matching user's reported time)
    # The user might be in a different timezone, but let's assume the server time matters.
    # Metadata says: 2026-01-16T08:21:15-05:00
    
    # We will simulate the prompt exactly as in app.py
    
    # Mocking "now" to be the time the user likely ran the test
    # If the user ran it "just now", it's Friday.
    # If the user asks for "Martes 11am".
    
    mock_now_iso = "2026-01-16T08:21:15"
    mock_day = "Friday"
    
    user_msg = "martes 11am"
    
    # Improved Prompt
    extraction_prompt = f"""
    Current Date: {mock_now_iso} ({mock_day})
    User Input: '{user_msg}'
    
    Task: Extract the intended appointment date and time in ISO format (YYYY-MM-DDTHH:MM).
    Rules:
    - If the user says a weekday (e.g., "Lunes", "Martes"), assume it refers to the UPCOMING {mock_day} or later.
    - If today is Friday and user says "Martes", it means next Tuesday (Jan 20).
    - Return ONLY the ISO string. No text. nothing else.
    - If valid date found, output format: YYYY-MM-DDTHH:MM
    - If uncertain or no date, output: FAIL
    """
    
    print(f"--- Prompt ---\n{extraction_prompt}\n")
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        res = model.generate_content(extraction_prompt).text.strip()
        print(f"--- Result ---\n{res}")
        
        # Parse result
        dt = datetime.fromisoformat(res)
        print(f"\nParsed Date: {dt.strftime('%A %Y-%m-%d')}")
        
        expected_date = "2026-01-20" # Next Tuesday
        if dt.strftime('%Y-%m-%d') == expected_date:
            print("STATUS: CORRECT ✅")
        else:
            print(f"STATUS: FAILURE ❌ (Expected {expected_date})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extraction()
