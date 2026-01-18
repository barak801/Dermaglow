import os
from dotenv import load_dotenv
from twilio.rest import Client

def test_twilio_outbound():
    load_dotenv()
    
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    
    # We'll try to send a message to the same from_number for testing 
    # (assuming it's the sandbox and user is registered)
    # If not, user will need to change 'to' number.
    
    if not all([sid, token, from_number]):
        print("❌ Missing Twilio credentials in .env")
        return

    try:
        client = Client(sid, token)
        # Test message
        message = client.messages.create(
            from_=from_number,
            body="Twilio connection test: SUCCESS! 💎",
            to=from_number # Sending to self as a basic ping test
        )
        print(f"✅ Message sent! SID: {message.sid}")
    except Exception as e:
        print(f"❌ Twilio Error: {e}")

if __name__ == "__main__":
    test_twilio_outbound()
