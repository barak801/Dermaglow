import os
import sys
import json
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, Message

FORBIDDEN_PHRASES = [
    "¿En qué puedo asistirle?",
    "Para asistirle mejor",
    "¿En qué puedo ayudarle?",
    "¿Tanto en qué puedo ayudarle?",
    "¿Desea conocer nuestra disponibilidad?",
    "¿Tiene alguna otra duda?",
    "¿Alguna otra pregunta?",
    "¿Desea agendar una cita?"
]

SOPHISTICATED_KEYWORDS = [
    "concierge",
    "transformación",
    "excelencia",
    "maestría",
    "exclusividad",
    "acredita",
    "coordinar",
    "agenda",
    "proceder",
    "valoración"
]

def analyze_response(step_name, response_text):
    print(f"\n--- Analyzing Response for Step: {step_name} ---")
    print(f"Response: {response_text}")
    
    # Check for forbidden phrases
    found_forbidden = [p for p in FORBIDDEN_PHRASES if p.lower() in response_text.lower()]
    if found_forbidden:
        print(f"❌ FAIL: Found forbidden phrases: {found_forbidden}")
    else:
        print("✅ PASS: No forbidden phrases found.")
        
    # Check for sophisticated tone (presence of at least one keyword)
    found_keywords = [k for k in SOPHISTICATED_KEYWORDS if k.lower() in response_text.lower()]
    if found_keywords:
        print(f"✅ PASS: Found sophisticated keywords: {found_keywords}")
    else:
        print("⚠️ WARNING: No sophisticated keywords found. Tone might be too simple.")

    # Check for robotic markers (like "Aquí tienes", "Claro,")
    robotic_markers = ["Aquí tienes", "Claro, puedo", "Soy un modelo de lenguaje"]
    found_markers = [m for m in robotic_markers if m.lower() in response_text.lower()]
    if found_markers:
        print(f"❌ FAIL: Found robotic markers: {found_markers}")
    else:
        print("✅ PASS: No robotic markers found.")

def test_fewshots():
    test_phone = "whatsapp:+999888777"
    
    with app.app_context():
        # Cleanup
        user = User.query.filter_by(phone_number=test_phone).first()
        if user:
            Message.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()

        with app.test_client() as client:
            # 1. Welcome State
            print("\n🚀 Testing WELCOME state...")
            res = client.post('/webhook/', data={'Body': 'Hola', 'From': test_phone})
            analyze_response("welcome", res.data.decode())

            # 2. Discovery State (with extraction)
            print("\n🚀 Testing DISCOVERY state...")
            res = client.post('/webhook/', data={'Body': '¿De qué se trata el endolifting?', 'From': test_phone})
            analyze_response("discovery", res.data.decode())

            # 3. Collect Info State
            print("\n🚀 Testing COLLECT_INFO state...")
            res = client.post('/webhook/', data={'Body': 'Me interesa agendar una cita', 'From': test_phone})
            analyze_response("collect_user_info", res.data.decode())

            # 4. Handle Deposit Objection
            print("\n🚀 Testing DEPOSIT_OBJECTION state...")
            # Set state manually to simulate objection context
            user = User.query.filter_by(phone_number=test_phone).first()
            user.current_flow_step = 'collect_user_info'
            db.session.commit()
            
            res = client.post('/webhook/', data={'Body': '¿Por qué tengo que pagar antes?', 'From': test_phone})
            analyze_response("handle_deposit_objection", res.data.decode())

if __name__ == "__main__":
    test_fewshots()
