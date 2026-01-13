import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv

# Import our custom modules
from models import db, Conversation, Message, KnowledgeBase, LeadSummary
from execution.twilio_security import validate_twilio_request
from execution.gemini_handler import GeminiHandler

import sys

# Load env vars
load_dotenv()

app = Flask(__name__)
# Force stdout to flush for real-time logging
sys.stdout.reconfigure(line_buffering=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dermaglow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Gemini
gemini = GeminiHandler()

@app.before_first_request
def create_tables():
    db.create_all()

def check_auth(username, password):
    """Verifies Basic Auth credentials."""
    return username == os.getenv('ADMIN_USER') and password == os.getenv('ADMIN_PASS')

@app.route('/webhooks/twilio', methods=['POST'])
@validate_twilio_request
def twilio_webhook():
    """
    Main webhook handler for Twilio (WhatsApp, Messenger, Instagram).
    """
    print(f"\n>>> WEBHOOK RECEIVED")
    incoming_msg = request.values.get('Body', '').lower()
    from_id = request.values.get('From', '')
    print(f"    Message: {incoming_msg}")
    print(f"    From: {from_id}")
    
    # 1. Retrieve or Create Conversation
    print("    Step 1: Checking conversation...")
    conv = Conversation.query.filter_by(user_id=from_id).first()
    if not conv:
        print(f"    Creating new conversation for {from_id}")
        conv = Conversation(user_id=from_id)
        db.session.add(conv)
        db.session.commit()
    print(f"    Conversation ID: {conv.id}")

    # 2. Check for Summarization Trigger (30 mins silence or 20 messages)
    now = datetime.utcnow()
    trigger_summarization = False
    if conv.message_count >= 20:
        trigger_summarization = True
    elif (now - conv.last_interaction) > timedelta(minutes=30) and conv.message_count > 0:
        trigger_summarization = True

    if trigger_summarization:
        # Get history for summary
        history = Message.query.filter_by(conversation_id=conv.id).all()
        summary_raw = gemini.summarize_conversation(history)
        
        # Parse summary (simplified)
        summary_text, key_interests = summary_raw.split('|') if '|' in summary_raw else (summary_raw, "")
        
        lead_sum = LeadSummary.query.filter_by(user_id=from_id).first()
        if not lead_sum:
            lead_sum = LeadSummary(user_id=from_id, summary_text=summary_text, key_interests=key_interests)
            db.session.add(lead_sum)
        else:
            lead_sum.summary_text = summary_text
            lead_sum.key_interests = key_interests
        
        # Reset count after summary
        conv.message_count = 0 
        db.session.commit()

    # 3. Store User Message
    print("    Step 3: Storing user message...")
    user_msg = Message(conversation_id=conv.id, role='user', content=incoming_msg)
    db.session.add(user_msg)
    conv.message_count += 1
    conv.last_interaction = now
    db.session.commit()
    print("    User message committed to DB.")

    # 4. Get RAG Response from Gemini
    print("    Step 4: Requesting response from Gemini (this may take a moment)...")
    # Fetch last 10 messages for context
    history = Message.query.filter_by(conversation_id=conv.id).order_by(Message.timestamp.desc()).limit(11).all()
    history.reverse() # Sort chronologically
    
    # Fetch Knowledge Base URIs
    kb_files = KnowledgeBase.query.all()
    file_uris = [f.file_uri for f in kb_files]

    ai_response_text = gemini.get_response(incoming_msg, history[:-1], file_uris)
    print(f"    Gemini response received: {ai_response_text[:50]}...")

    # 5. Store AI Response
    ai_msg = Message(conversation_id=conv.id, role='agent', content=ai_response_text)
    db.session.add(ai_msg)
    db.session.commit()

    # 6. Respond to Twilio
    resp = MessagingResponse()
    resp.message(ai_response_text)
    return str(resp)

@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    """
    RAG Admin Panel: Upload Knowledge Base files to Gemini.
    """
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return ('Could not verify your access level for that URL.\n'
                'You have to login with proper credentials', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})

    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400
        
        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Upload to Gemini File API
            file_uri = gemini.upload_file(filepath, display_name=filename)
            
            new_kb = KnowledgeBase(file_name=filename, file_uri=file_uri)
            db.session.add(new_kb)
            db.session.commit()
            return redirect(url_for('admin_upload'))

    kb_items = KnowledgeBase.query.all()
    # Simple HTML Template (inline for speed, usually goes in templates/)
    kb_list_html = "".join([f"""
        <li>
            {item.file_name} ({item.file_uri}) 
            <form method="post" action="{url_for('admin_delete', file_id=item.id)}" style="display:inline;">
                <button type="submit" onclick="return confirm('Delete this file?')">Delete</button>
            </form>
        </li>""" for item in kb_items])

    return f"""
    <h1>Dermaglow RAG Admin</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit" value="Upload to KB">
    </form>
    <hr>
    <h3>Knowledge Base Files:</h3>
    <ul>
      {kb_list_html}
    </ul>
    """

@app.route('/admin/delete/<int:file_id>', methods=['POST'])
def admin_delete(file_id):
    """
    RAG Admin Panel: Delete a file from Gemini and DB.
    """
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return ('Access Denied', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

    kb_item = KnowledgeBase.query.get_or_404(file_id)
    
    # Delete from Gemini
    gemini.delete_file(kb_item.file_uri)
    
    # Delete from DB
    db.session.delete(kb_item)
    db.session.commit()
    
    return redirect(url_for('admin_upload'))

if __name__ == '__main__':
    app.run(debug=True)
