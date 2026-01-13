import os
import requests
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv

# Load configuration
load_dotenv()

def send_mock_request(body, from_id="whatsapp:+123456789", url="http://127.0.0.1:5000/webhooks/twilio"):
    """
    Sends a signed request to the local webhook endpoint.
    """
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not auth_token:
        print("Error: TWILIO_AUTH_TOKEN not found in .env")
        return

    # Payloads in Twilio are sent as FORM data
    payload = {
        'Body': body,
        'From': from_id,
        'To': 'whatsapp:+1987654321', # Dummy destination
        'MessageSid': 'SM1234567890abcdef',
        'AccountSid': 'AC1234567890abcdef'
    }

    # Generate the signature
    validator = RequestValidator(auth_token)
    signature = validator.compute_signature(url, payload)

    # Headers
    headers = {
        'X-Twilio-Signature': signature,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    print(f"Sending request to {url}...")
    print(f"Payload: {payload}")
    print("Waiting for response from server (Gemini call may take some time)...")
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        print(f"\n<<< RESPONSE RECEIVED")
        print(f"Status Code: {response.status_code}")
        print("Response XML:")
        print(response.text)
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Is app.py running?")

if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "Hola, ¿que es la Mela?"
    send_mock_request(msg)
