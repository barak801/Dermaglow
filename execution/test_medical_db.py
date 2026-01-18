import requests
import time

def test_medical_knowledge():
    print("--- TESTING MEDICAL INTELLIGENCE (DATABASE INTEGRATION) ---")
    
    # Simulate a user asking about a procedure from the DB
    payload = {
        "From": "whatsapp:+777888999",
        "Body": "¿Cuánto dura la liposucción con microaire y qué beneficios tiene?"
    }
    
    try:
        response = requests.post("http://localhost:5000/webhook/", data=payload)
        print(f"Status: {response.status_code}")
        print(f"Jesica says:\n{response.text}")
    except Exception as e:
        print(f"Error connecting to webhook: {e}")

if __name__ == "__main__":
    test_medical_knowledge()
