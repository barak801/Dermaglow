import requests
import sys

def test_webhook(message, phone="573000000000"):
    url = "http://127.0.0.1:5000/webhook/"
    data = {"Body": message, "From": f"whatsapp:{phone}"}
    response = requests.post(url, data=data)
    return response.text

if __name__ == "__main__":
    print("--- STARTING VERIFICATION ---")
    
    # 1. Start fresh
    print("\n1. Greeting:")
    print(test_webhook("Hola Jesica"))
    
    # 2. Inquiry
    print("\n2. Inquiry about Endolifting:")
    print(test_webhook("Me interesa un Endolifting facial"))
    
    # 3. Provide Info
    print("\n3. Providing user info:")
    print(test_webhook("Soy Juan Perez, juan@gmail.com, cedula 555666"))
    
    # 4. Request Slot
    print("\n4. Requesting time (Mañana a las 10am):")
    # Note: This depends on current time, but 'tomorrow' is usually safe
    print(test_webhook("Para mañana a las 10am"))
    
    print("\n--- VERIFICATION FINISHED ---")
