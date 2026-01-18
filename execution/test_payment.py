import requests

def test_payment(phone="573000000000"):
    url = "http://127.0.0.1:5000/webhook/"
    data = {
        "Body": "Aquí está mi comprobante", 
        "From": f"whatsapp:{phone}",
        "NumMedia": "1",
        "MediaUrl0": "https://api.twilio.com/2010-04-01/Accounts/AC.../Messages/MM.../Media/ME..." # Placeholder
    }
    response = requests.post(url, data=data)
    return response.text

if __name__ == "__main__":
    print("--- TESTING PAYMENT VERIFICATION ---")
    print(test_payment())
    print("\n--- TEST FINISHED ---")
