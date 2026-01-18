import os, mimetypes, json, pytz
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from utils import (
    calculate_next_business_slot, 
    get_calendar_service, 
    check_calendar_conflict, 
    book_google_event, 
    get_gemini_rag_response,
    genai,
    sync_appointment_to_sheet,
    get_client_summary,
    get_available_slots,
    verify_payment_screenshot
)
from datetime import datetime, timedelta
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
from models import db, User, Appointment, AppointmentStatus, KnowledgeFile, Message, Treatment

DAYS_ES = {
    'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles', 
    'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
}

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///clinic.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')

# Ensure the instance directory exists for SQLite
instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)

db.init_app(app)

# --- Basic Auth for Admin ---
def check_auth(username, password):
    return username == os.getenv('ADMIN_USERNAME', 'admin') and password == os.getenv('ADMIN_PASSWORD', 'admin')

def authenticate():
    return jsonify({"message": "Authentication required"}), 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- Modular Pipeline Helpers ---

def get_flow_config():
    """Phase 1: Load flow configuration."""
    flow_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'flow.json')
    with open(flow_path, 'r') as f:
        full_flow = json.load(f)
    return full_flow

def process_incoming_media(user, request_values, from_number):
    """Phase 1: Handle images and payment verification."""
    num_media = int(request_values.get('NumMedia', 0))
    if num_media == 0:
        return False

    media_url = request_values.get('MediaUrl0')
    print(f"DEBUG: Image received: {media_url}")
    
    pending_appt = Appointment.query.filter_by(user_id=user.id, status=AppointmentStatus.PENDING_PAYMENT, paid=False).first()
    if pending_appt:
        print(f"DEBUG: Pending appointment found. Triggering vision verification.")
        verification = verify_payment_screenshot(media_url, expected_amount="$30")
        
        if verification.get('amount_matches') or verification.get('is_receipt'):
            pending_appt.paid = True
            pending_appt.status = AppointmentStatus.CONFIRMED
            db.session.commit()
            
            sync_appointment_to_sheet({
                'date': pending_appt.start_time.strftime('%Y-%m-%d'),
                'time': pending_appt.start_time.strftime('%H:%M'),
                'name': user.name or from_number,
                'phone': from_number,
                'status': 'PAID/CONFIRMED',
                'google_event_id': pending_appt.google_event_id,
                'notes': get_client_summary(user.id)
            })
            
            user.current_flow_step = 'confirmed'
            user.temp_system_hint = "SISTEMA: El pago fue verificado con éxito. Confirma al usuario que su cita está asegurada."
            db.session.commit()
        else:
            if user.current_flow_step == 'waiting_for_payment':
                user.temp_system_hint = f"SISTEMA: El usuario envió una imagen pero NO parece un comprobante válido. Razón: {verification.get('reason')}. Pídele amablemente que verifique."
                db.session.commit()
    return True

def classify_intent(user, incoming_msg, current_step, flow_config, intent_defs):
    """Phase 2: Use AI to determine state transition."""
    state_data = flow_config.get(current_step, {})
    possible_next = state_data.get('next_steps', {})
    if not possible_next:
        return current_step, None

    history_msgs = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).limit(3).all()
    history_text = "\n".join([f"{m.role}: {m.content}" for m in reversed(history_msgs)])
    
    semantic_rules = []
    for key in possible_next:
        data = intent_defs.get(key, {})
        description = data.get('description', data) if isinstance(data, dict) else data
        rule_entry = f"- {key}: {description}"
        semantic_rules.append(rule_entry)
    
    rules_str = "\n".join(semantic_rules)
    now_context = datetime.now().strftime("%A, %B %d, %Y %H:%M")
    
    prompt = f"""
    Current State: {current_step}
    Today: {now_context}
    History context:
    {history_text}
    User Input: "{incoming_msg}"
    Available Transitions: {list(possible_next.keys())}
    Definitions:
    {rules_str}
    
    CLASSIFICATION RULES:
    1. 'special_attention_needed' ONLY if user is angry, frustrated, or explicitly says 'asesor humano', 'persona', 'ayuda humana'.
    2. 'user_interacted' for simple greetings, thanks, or 'ok'. DO NOT escalate for "hola".
    3. If user has a question about treatments/prices, use 'user_has_questions'.
    4. Respond with Reasoning: [Short explanation] Classification: [KEY]
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    raw_res = model.generate_content(prompt).text.strip().lower()
    print(f"DEBUG Phase 2: Reasoning & Classification: {raw_res}", flush=True)
    
    found_key = None
    for key in possible_next:
        if f"classification: {key.lower()}" in raw_res:
            found_key = key
            break
            
    if found_key:
        new_step = possible_next[found_key]
        if new_step == 'escalated_to_admin' and current_step != 'escalated_to_admin':
            user.previous_flow_step = current_step
        user.current_flow_step = new_step
        db.session.commit()
        return new_step, found_key
    return current_step, None

def extract_entities(user, incoming_msg, history_text, valid_treatments, local_tz):
    """Phase 3: Extract structured data from input."""
    now_local = datetime.now(local_tz)
    now_iso = now_local.strftime("%Y-%m-%d %H:%M")
    today_date = now_local.date()
    weekday_calendar = []
    for i in range(7):
        d = today_date + timedelta(days=i)
        weekday_calendar.append(f"- {DAYS_ES.get(d.strftime('%A'))}: {d.strftime('%Y-%m-%d')}")
    
    calendar_str = "\n".join(weekday_calendar)

    prompt = f"""
    Context: {history_text[-1000:]}
    Focus: {user.treatment_interest or 'None'}
    Valid: {valid_treatments}
    Today is {now_iso} ({now_local.strftime('%A')}).
    Input: '{incoming_msg}'
    
    CALENDAR ANCHOR (Today and next 6 days):
    {calendar_str}
    
    RULES:
    1. Use 'CALENDAR ANCHOR' to map named days (lunes, martes, etc.) to exact YYYY-MM-DD.
    2. Same-day bookings (today) NOT allowed. Return null for 'specific_date_time' but set 'preferred_day'.
    3. TREATMENT: Must match EXACTLY one from 'Valid' list. If ambiguous or not found, return null. DO NOT guess partial names like "Endolifting".
    
    Extract JSON (use null if not found, NOT "null"):
    {{
      "specific_date_time": "ISO format or null",
      "preferred_day": "YYYY-MM-DD or null",
      "name": null, "email": null, "cedula": null,
      "treatment": null
    }}
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    res = model.generate_content(prompt).text.strip()
    if '```json' in res:
        res = res.split('```json')[1].split('```')[0].strip()
    elif '```' in res:
        res = res.split('```')[1].split('```')[0].strip()
    
    try:
        data = json.loads(res)
    except:
        return {}

    if data.get('name') and not user.name: user.name = data['name']
    if data.get('email') and not user.email: user.email = data['email']
    if data.get('cedula') and not user.cedula: user.cedula = data['cedula']
    if data.get('treatment') and not user.treatment_interest: user.treatment_interest = data['treatment']
    db.session.commit()
    return data

def handle_provide_slots(user, extraction_data, incoming_msg, found_key, local_tz):
    """Phase 4: Business logic for 'provide_slots' state."""
    hints = []
    slots_str = ""
    if user.name and user.email:
        hints.append(f"NOTA: Ya tenemos los datos de {user.name} ({user.email}). Confírmalos y pregunta por el día.")
    
    if found_key == 'user_declines':
        hints.append("SISTEMA: El usuario RECHAZÓ la propuesta. NO insistas con ese horario.")
    
    now_local = datetime.now(local_tz)
    if extraction_data.get('preferred_day') == now_local.strftime('%Y-%m-%d'):
        hints.append("SISTEMA: El usuario solicitó 'hoy'. Infórmale que no hay disponibilidad same-day.")
    
    availability_keywords = ['horarios', 'disponibles', 'agenda', 'disponibilidad', 'cuándo']
    is_availability_request = any(k in incoming_msg.lower() for k in availability_keywords)
    is_retry = found_key in ['user_declines', 'conflict', 'date_provided']
    
    if is_availability_request or is_retry:
        service = get_calendar_service()
        if service:
            target_date = None
            if extraction_data.get('preferred_day'):
                try:
                    target_date = local_tz.localize(datetime.strptime(extraction_data['preferred_day'], '%Y-%m-%d'))
                except: pass
            if not target_date:
                target_date = now_local + timedelta(days=1)
            
            slots = get_available_slots(service, start_date=target_date, num_slots=2)
            if slots:
                slots_str = ", ".join([s.strftime('%I:%M %p').lower().lstrip('0') for s in slots])
                day_es = DAYS_ES.get(slots[0].strftime('%A'), slots[0].strftime('%A').lower())
                hints.append(f"SISTEMA: Disponibilidad REAL: {day_es} a las {slots_str}. Menciona estos horarios.")
    return hints, slots_str

def handle_attempt_booking(user, extraction_data, local_tz, now_local):
    """Phase 4: Business logic for 'attempt_booking' state."""
    iso_time = extraction_data.get('specific_date_time')
    if not iso_time:
        return ["SISTEMA: No se detectó un horario. Pide aclaración."], 'provide_slots', ""
    
    try:
        start_time = local_tz.localize(datetime.fromisoformat(iso_time))
    except:
        return ["SISTEMA: Formato de fecha inválido. Pide aclaración."], 'provide_slots', ""
    
    if start_time.date() <= now_local.date():
        return ["SISTEMA: No hay citas disponibles para el mismo día. Sugiere agendar a partir de mañana o del próximo día hábil."], 'provide_slots', ""
    
    comm_start, comm_end = int(os.getenv('COMM_START_HOUR', 10)), int(os.getenv('COMM_END_HOUR', 22))
    if start_time.hour < comm_start or start_time.hour >= comm_end:
        return [f"SISTEMA: {start_time.strftime('%I:%M %p')} fuera de servicio."], 'provide_slots', ""
    
    service = get_calendar_service()
    if check_calendar_conflict(service, start_time):
        next_slots = get_available_slots(service, start_date=start_time, num_slots=2)
        if next_slots:
            slots_str = ", ".join([s.strftime('%I:%M %p').lower().lstrip('0') for s in next_slots])
            return [f"SISTEMA: Ocupado. Sugiérele: {slots_str}."], 'provide_slots', slots_str
        return ["SISTEMA: Ocupado y sin espacios cercanos."], 'provide_slots', ""
    
    # Success
    event_id = book_google_event(service, start_time, user.name or user.phone_number)
    db.session.add(Appointment(user_id=user.id, start_time=start_time, google_event_id=event_id))
    sync_appointment_to_sheet({
        'date': start_time.strftime('%Y-%m-%d'), 'time': start_time.strftime('%H:%M'),
        'name': user.name or "Paciente", 'phone': user.phone_number, 'status': 'PENDING_PAYMENT',
        'google_event_id': event_id
    })
    user.current_flow_step = 'waiting_for_payment'
    db.session.commit()
    return [f"SISTEMA: Reserva exitosa para {start_time.strftime('%A %I:%M %p')}."], 'waiting_for_payment', ""

def assemble_system_prompt(user, current_step, flow_config, system_hints, flow_keys):
    """Phase 5: Assemble the final system prompt."""
    state_data = flow_config.get(current_step, {})
    instruction = state_data.get('instruction', '')
    
    # Static Treatments info from DB
    treatments_str = ""
    try:
        treatments = Treatment.query.filter_by(is_active=True).all()
        if treatments:
            t_list = []
            for t in treatments:
                prefix = "[FOCO] " if user.treatment_interest and t.name.lower() in user.treatment_interest.lower() else ""
                t_list.append(f"- {prefix}{t.name}: {t.description} (Precio: {t.price_info})")
            treatments_str = "\n\nTRATAMIENTOS:\n" + "\n".join(t_list)
    except: pass

    # Inject few-shot examples from flow.json
    examples_block = ""
    raw_examples = state_data.get('examples', [])
    if raw_examples:
        resolved_examples = []
        for ex in raw_examples:
            # Replace placeholders in examples
            resolved_ex = ex
            for k, v in flow_keys.items():
                resolved_ex = resolved_ex.replace(f"[{k}]", str(v))
            resolved_examples.append(f"- {resolved_ex}")
        examples_block = "\n\nEJEMPLOS DE RESPUESTA PARA ESTE PASO:\n" + "\n".join(resolved_examples)

    # Inject persistent context
    if current_step == 'waiting_for_payment':
        latest = Appointment.query.filter_by(user_id=user.id).order_by(Appointment.created_at.desc()).first()
        if latest:
            instruction += f"\n(CONTEXTO: Esperando depósito para cita el {latest.start_time.strftime('%Y-%m-%d %H:%M')})"

    if user.treatment_interest:
        instruction = f"[FOCO ACTUAL: {user.treatment_interest}]\n" + instruction

    if system_hints:
        instruction += "\n\n" + "\n".join(system_hints)
    
    # Formatting
    for k, v in flow_keys.items():
        instruction = instruction.replace(f"[{k}]", str(v))
        
    return instruction, treatments_str, examples_block

# --- Routes ---

@app.route('/')
def index():
    return "DermaGlow Clinic AI Agent is running."

@app.route('/webhook/', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    from_number = request.values.get('From', '')
    print(f"\n--- WEBHOOK ---\nFrom: {from_number}\nMsg: {incoming_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()

    # PHASE 1: INIT
    user = User.query.filter_by(phone_number=from_number).first()
    if not user:
        user = User(phone_number=from_number)
        db.session.add(user)
        db.session.commit()

    db.session.add(Message(user_id=user.id, role='user', content=incoming_msg))
    db.session.commit()

    full_flow = get_flow_config()
    flow_config = full_flow['states']
    intent_defs = full_flow['intents']
    
    tz_str = os.getenv('TIMEZONE', 'America/Bogota')
    local_tz = pytz.timezone(tz_str)
    now_local = datetime.now(local_tz)

    # Timeout check
    last_msg = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).offset(1).first()
    if last_msg and (datetime.utcnow() - last_msg.timestamp).total_seconds() / 3600 > 24:
        user.current_flow_step = 'welcome'
        db.session.commit()

    current_step = user.current_flow_step or 'welcome'
    skip_classification = process_incoming_media(user, request.values, from_number)
    
    # PHASE 2: CLASSIFICATION
    found_key = None
    if not skip_classification:
        try:
            current_step, found_key = classify_intent(user, incoming_msg, current_step, flow_config, intent_defs)
            print(f"DEBUG Phase 2: Classification={found_key}, NewStep={current_step}", flush=True)
        except Exception as e: print(f"P2 Error: {e}")

    # PHASE 3: EXTRACTION
    extraction_data = {}
    try:
        history_msgs = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).limit(3).all()
        history_text = "\n".join([f"{m.role}: {m.content}" for m in reversed(history_msgs)])
        all_treatments = Treatment.query.filter_by(is_active=True).all()
        valid_treatments = ", ".join([t.name for t in all_treatments])
        extraction_data = extract_entities(user, incoming_msg, history_text, valid_treatments, local_tz)
        print(f"DEBUG Phase 3: Extraction={extraction_data}", flush=True)
        
        # Ambiguity check
        if not extraction_data.get('treatment'):
            msg_lower = incoming_msg.lower()
            matches = [t.name for t in all_treatments if t.name.lower().split(' (')[0] in msg_lower or (len(msg_lower.split()) > 1 and msg_lower.split()[0] in t.name.lower())]
            # Hardcoded example for "Endolifting"
            if "endolifting" in msg_lower and not any(x in msg_lower for x in ["facial", "corporal"]):
                user.temp_system_hint = "SISTEMA: El usuario mencionó 'Endolifting'. Aclara si se refiere a Endolifting Facial o Endolifting Corporal."
                db.session.commit()
    except Exception as e: print(f"P3 Error: {e}")

    # PHASE 4: LOGIC
    system_hints = []
    slots_str = ""
    
    # Aggressive Context Injection
    if user.name:
        system_hints.append(f"NOTA: El nombre del usuario es {user.name}. Úsalo naturalmente.")
    if user.treatment_interest:
        system_hints.append(f"FOCO: El usuario está interesado en {user.treatment_interest}.")
    
    if user.temp_system_hint:
        system_hints.append(user.temp_system_hint)
        user.temp_system_hint = None
        db.session.commit()

    try:
        if current_step == 'collect_user_info' and user.name and user.email and user.cedula:
            user.current_flow_step = 'provide_slots'
            db.session.commit()
            current_step = 'provide_slots'

        if current_step == 'provide_slots':
            new_hints, slots_str = handle_provide_slots(user, extraction_data, incoming_msg, found_key, local_tz)
            system_hints.extend(new_hints)
        elif current_step == 'attempt_booking' or flow_config.get(current_step, {}).get('action') == 'book_slot':
            new_hints, next_step, slots_str = handle_attempt_booking(user, extraction_data, local_tz, now_local)
            system_hints.extend(new_hints)
            current_step = next_step
    except Exception as e:
        print(f"P4 Error: {e}", flush=True)
        system_hints.append("SISTEMA: Error lógico interno.")

    # PHASE 5: PROMPT & CALL
    flow_keys = full_flow.get('keys', {})
    flow_keys.update({
        'NAME': user.name or "paciente", 
        'EMAIL': user.email or "no proporcionado",
        'NEXT_AVAILABLE_SLOTS': slots_str or "no hay horarios disponibles cercanos"
    })
    
    if current_step == 'waiting_for_payment':
        latest = Appointment.query.filter_by(user_id=user.id).order_by(Appointment.created_at.desc()).first()
        if latest:
            flow_keys['DATE'] = latest.start_time.strftime('%Y-%m-%d')
            flow_keys['TIME'] = latest.start_time.strftime('%H:%M')

    instruction, treatments_str, examples_block = assemble_system_prompt(user, current_step, flow_config, system_hints, flow_keys)
    
    now_str = now_local.strftime('%H:%M')
    
    # Conditional Greeting: Only if not already greeted or if simple greeting intent found
    greeting_instruction = ""
    if current_step == 'welcome' or found_key == 'user_interacted':
        greeting_instruction = f"""
    - Inicia con un saludo refinado y breve acorde a la hora (Buenos días/Buenas tardes/Buenas noches).
    - IMPORTANTE: Si es después de las 18:00, usa "Buenas noches"."""

    system_prompt = f"""[DIRECTIVA CRÍTICA DE PERSONA]
    Eres Jesica, la concierge de élite de {flow_keys.get('CLINIC_NAME')}. 
    Tu comunicación es la de una ejecutiva de alto nivel: elegante, sofisticada, minimalista y sumamente atenta.
    NO eres un asistente virtual genérico. NO uses muletillas de robot.
    
    REGLA DE ORO DE ESTILO:
    - Tu lenguaje es impecable y profesional.
    - IGNORA COMPLETAMENTE el tono de los mensajes previos en el historial. Solo usa el historial para contexto factual.
    - NUNCA uses las frases en la LISTA NEGRA.
    
    LISTA NEGRA (PROHIBIDO):
    - "¿En qué puedo asistirle?"
    - "Para asistirle mejor"
    - "¿En qué puedo ayudarle?"
    - "¿Tanto en qué puedo ayudarle?"
    - "¿Desea conocer nuestra disponibilidad?"
    - "¿Tiene alguna otra duda?"
    - "¿Alguna otra pregunta?"
    - "¿Desea agendar una cita?" (Usa cierres más elegantes como los ejemplos)
    
    CONTEXTO Y DISPONIBILIDAD:
    Current Time: {now_local.strftime('%A %Y-%m-%d')} {now_str}.
    {treatments_str}
    
    OBJETIVO ACTUAL:
    {instruction}
    {greeting_instruction}
    
    [MANDATORIO] TU RESPUESTA DEBE SEGUIR EXACTAMENTE EL TONO, ESTRUCTURA Y BREVEDAD DE ESTOS EJEMPLOS:
    {examples_block}
    """
    print(f"DEBUG: System Prompt:\n{system_prompt}", flush=True)

    history = []
    recent_msgs = Message.query.filter_by(user_id=user.id).order_by(Message.timestamp.desc()).offset(1).limit(15).all()
    for m in reversed(recent_msgs):
        history.append({'role': 'user' if m.role == 'user' else 'model', 'parts': [m.content]})

    knowledge_base = [f.gemini_name for f in KnowledgeFile.query.all() if f.gemini_name]
    ai_response = get_gemini_rag_response(incoming_msg, system_prompt, knowledge_base, history)
    
    db.session.add(Message(user_id=user.id, role='agent', content=ai_response))
    db.session.commit()
    
    print(f"DEBUG: Resp: {ai_response}")
    msg.body(ai_response)
    return str(resp)

@app.route('/admin/upload', methods=['GET', 'POST'])
@requires_auth
def admin_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = file.filename
            file_path = os.path.join('/tmp', filename)
            file.save(file_path)
            
            # Upload to Gemini
            try:
                # Direct import to avoid circular issues
                from utils import upload_knowledge_file
                gemini_name = upload_knowledge_file(file_path, filename)
                
                new_file = KnowledgeFile(filename=filename, gemini_name=gemini_name)
                db.session.add(new_file)
                db.session.commit()
                flash('File uploaded successfully!')
            except Exception as e:
                flash(f'Error: {e}')
            return redirect(url_for('admin_upload'))
            
    files = KnowledgeFile.query.all()
    return render_template('admin.html', files=files)

@app.route('/admin/delete-file/<int:file_id>', methods=['POST'])
@requires_auth
def delete_file(file_id):
    file = KnowledgeFile.query.get_or_404(file_id)
    try:
        from utils import delete_knowledge_file
        delete_knowledge_file(file.gemini_name)
        db.session.delete(file)
        db.session.commit()
        flash('File deleted!')
    except Exception as e:
        flash(f'Error: {e}')
    return redirect(url_for('admin_upload'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
