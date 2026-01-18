import requests
import sys
import hmac
import hashlib
import base64
import os
from dotenv import load_dotenv

load_dotenv()

def generate_signature(url, data, auth_token):
    # Sort data by key for Twilio signature validation
    encoded_data = "".join([f"{k}{v}" for k, v in sorted(data.items())])
    raw_signature = url + encoded_data
    
    mac = hmac.new(auth_token.encode('utf-8'), raw_signature.encode('utf-8'), hashlib.sha1)
    return base64.b64encode(mac.digest()).decode('utf-8')

def mock_request(message_body):
    url = "http://127.0.0.1:5000/webhook/"
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'placeholder_token')
    
    data = {
        'Body': message_body,
        'From': 'whatsapp:+573161154777',
        'To': 'whatsapp:+14155238886',
        'MessageSid': 'SM1234567890abcdef',
        'AccountSid': os.getenv('TWILIO_ACCOUNT_SID', 'ACplaceholder'),
        'NumMedia': '0'
    }
    
    signature = generate_signature(url, data, auth_token)
    headers = {'X-Twilio-Signature': signature}
    
    print(f"Sending request to {url}...")
    print(f"Payload: {data}")
    
    try:
        response = requests.post(url, data=data, headers=headers)
        print(f"\n<<< RESPONSE RECEIVED")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Hola"
    mock_request(msg)
