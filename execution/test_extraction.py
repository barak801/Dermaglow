import os
import json
import google.generativeai as genai
from datetime import datetime
import pytz
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def test_extraction(user_input, history=""):
    tz_str = os.getenv('TIMEZONE', 'America/Bogota')
    local_tz = pytz.timezone(tz_str)
    now_local = datetime.now(local_tz)
    now_iso = now_local.strftime("%Y-%m-%d %H:%M")
    
    extraction_prompt = f"""
    Context: {history}
    
    Today is {now_iso} ({now_local.strftime('%A')}).
    Latest User Message: '{user_input}'
    
    Based on the message and context, extract the following entities in JSON format:
    {{
      "specific_date_time": "ISO format YYYY-MM-DDTHH:MM if the user specified a clear time or picked one from the options (e.g. '10:00 AM' or 'the second option'), else null",
      "preferred_day": "YYYY-MM-DD format if the user mentioned a day, else null",
      "name": "Full name or null",
      "email": "Email address or null"
    }}
    Return ONLY the JSON.
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(extraction_prompt).text.strip()
    print(f"Input: {user_input}")
    print(f"Output: {response}")

if __name__ == "__main__":
    test_extraction("2", history="Agent: Tenemos disponibles las 10:00 AM y las 3:00 PM de este sábado 17 de enero.")
    test_extraction("la primera", history="Agent: Tenemos disponibles las 10:00 AM y las 3:00 PM de este sábado 17 de enero.")
