import os
import sys
import json

# Add current directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, User, Message, Treatment
from flask import request

def test_prompt_generation():
    with app.app_context():
        # Create a dummy user
        user = User.query.filter_by(phone_number='12345').first()
        if not user:
            user = User(phone_number='12345', name='John Doe', treatment_interest='Endolifting Facial')
            db.session.add(user)
            db.session.commit()
        
        # Add a dummy message
        db.session.add(Message(user_id=user.id, role='user', content='Hola, quiero agendar una cita'))
        db.session.commit()
        
        # Simulate webhook context
        with app.test_request_context('/webhook/', data={'Body': 'Hola', 'From': '12345'}):
            # We can't easily call webhook() because it returns a Twilio response
            # But we can call the internal assemble_system_prompt directly if we export it correctly
            # or just look at the logs if we run it.
            # For this test, let's just import and call it if possible.
            from app import assemble_system_prompt, get_flow_config
            
            full_flow = get_flow_config()
            flow_config = full_flow['states']
            flow_keys = full_flow.get('keys', {})
            flow_keys.update({
                'NAME': user.name or "patient", 
                'EMAIL': user.email or "not provided",
                'NEXT_AVAILABLE_SLOTS': "Monday at 10am"
            })
            
            current_step = 'welcome'
            system_hints = ["NOTE: User is John Doe.", "FOCUS: Endolifting Facial."]
            
            instruction, treatments_str, examples_block = assemble_system_prompt(user, current_step, flow_config, system_hints, flow_keys)
            
            # This logic is copied from app.py to see the final output
            greeting_instruction = f"""
    - Start with a refined and brief greeting according to the time (Good morning/Good afternoon/Good evening).
    - IMPORTANT: If it's after 18:00, use "Buenas noches" (Spanish)."""

            system_prompt = f"""[PERSONA DIRECTIVE: EXPERT COORDINATOR]
    You are the Patient Coordinator for {flow_keys.get('CLINIC_NAME')}. 
    Your communication is that of a clinical expert: professional, clear, confident, and reassuring.
    You speak with the simplicity of someone who masters their field, avoiding unnecessary adornments (corporate fluff) while maintaining clinical standards of excellence.

    [LANGUAGE RULE] 
    STRICT REQUIREMENT: You MUST ALWAYS respond in SPANISH (Ecuador dialect). 
    While these instructions are in English, your actual output to the patient must be natural, high-level clinical Spanish.

    GOLDEN STYLE RULES:
    1. ELEVATE THE TONE: If the user is informal or enthusiastic, acknowledge their energy briefly but keep the conversation at a professional and clinical level.
    2. DYNAMISM IN BREVITY: 
       - Be brief and direct regarding logistics (scheduling, data, payments).
       - Be detailed, pedagogical, and reassuring when answering questions about medical procedures or results.
    3. NATURAL LANGUAGE: Use sophisticated Ecuadorian/neutral Spanish. Avoid English loanwords or phrases that sound like machine translation.

    BLACK LIST & REPLACEMENTS (MANDATORY):
    - FORBIDDEN: "¿En qué puedo ayudarle?" -> USE: "¿Qué información necesita sobre nuestros procedimientos?"
    - FORBIDDEN: "¿Desea agendar una cita?" -> USE: "Podemos reservar un espacio para su valoración cuando usted guste."
    - FORBIDDEN: Robotic fill-ins like "Para asistirle mejor" or "¿Tiene alguna otra duda?".

    CONTEXT & AVAILABILITY:
    Current Time: Monday 2026-01-21 19:15.
    {treatments_str}

    CURRENT STEP OBJECTIVE:
    {instruction}
    {greeting_instruction}

    [MANDATORY] YOUR RESPONSE MUST STRICTLY FOLLOW THE NEW CLINICAL COORDINATOR TONE. USE THESE EXAMPLES AS AN ANCHOR:
    {examples_block}
    """
            print("--- FINAL SYSTEM PROMPT ---")
            print(system_prompt)
            print("--- END PROMPT ---")

            # Final check: Is there any Spanish in the prompt that shouldn't be?
            # (Excluding the Spanish quotes in Black List and Greeting rule)
            
if __name__ == '__main__':
    test_prompt_generation()
