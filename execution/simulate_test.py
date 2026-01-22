import os, sys, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db, User, Message
import requests

def simulate_chat(phone, messages):
    print(f"\n--- 🧪 SIMULATING CONVERSATION FOR {phone} ---")
    webhook_url = "http://127.0.0.1:5000/webhook/"
    
    for msg in messages:
        print(f"👤 User: {msg}")
        payload = {
            'From': phone,
            'Body': msg
        }
        response = requests.post(webhook_url, data=payload)
        # Parse TwiML to get response body
        res_text = response.text
        if "<Body>" in res_text:
            agent_msg = res_text.split("<Body>")[1].split("</Body>")[0]
            print(f"🤖 Jesica: {agent_msg}\n")
        else:
            print(f"⚠️ Error: No TwiML body found. Response: {res_text}\n")

if __name__ == "__main__":
    # Test Scenario 1: Interest in Mela + Deep Questions
    test_user_1 = "whatsapp:+111222333"
    scenario_1 = [
        "Hola, buenas tardes",
        "Me interesa la Mela minilipo. ¿Qué zonas se pueden tratar?",
        "¿Duele mucho el procedimiento? Me da un poco de miedo",
        "Mi nombre es Maria Garcia, cedula 0987654321, mgarcia@test.com. Quiero agendar para el lunes a las 10 am"
    ]
    
    # Reset test users first
    with app.app_context():
        u1 = User.query.filter_by(phone_number=test_user_1).first()
        if u1:
            Message.query.filter_by(user_id=u1.id).delete()
            db.session.delete(u1)
            db.session.commit()
            print(f"Reset test user {test_user_1}")

    simulate_chat(test_user_1, scenario_1)
    
    # Verify Summary
    with app.app_context():
        u1 = User.query.filter_by(phone_number=test_user_1).first()
        if u1:
            print(f"📜 PERSISTENT SUMMARY GENERATED:\n{u1.summary}\n")
