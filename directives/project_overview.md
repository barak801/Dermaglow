# Role
Act as a Senior Python Backend Engineer. We are building a "Unified Social AI Agent" for a high-end aesthetic clinic.
**Business Name:** Clinica Estetica Dermaglow.
**Persona:** "High-End Concierge" (Polished, professional, exclusive, efficient).

# Objective
Create a Flask application hosted on cPanel that:
1.  **Omnichannel Communication:** Handles client interaction via Twilio (WhatsApp, Facebook Messenger, Instagram).
2.  **AI Brain (RAG):** Uses Google Gemini with the File API for deep knowledge retrieval to answer clinic-specific questions.
3.  **Smart Scheduling:** Integrates with Google Calendar to check availability, handle conflicts, and book/cancel appointments automatically.
4.  **Payment Verification Flow:** Enforces a strict "Active Window" flow for $30 booking deposits, with automated reminders and cancellations based on business hours.
5.  **Proof of Payment:** Automatically confirms appointments upon receipt of a payment screenshot (image handling).
6.  **Admin Control:** Provides a secure Admin Panel to manage the Knowledge Base (Upload/Delete files).
7.  **Service Stability:** Includes a cron system for background task processing (Reminders/Cancellations).

# Tech Stack
- **Framework:** Flask (Must be cPanel/Passenger compatible).
- **Database:** SQLite (SQLAlchemy).
- **APIs:**
    - `twilio` (Messaging).
    - `google-generativeai` (Gemini & File Search).
    - `google-api-python-client` (Google Calendar & Sheets).

# 1. The Brain (AI & Persona)
- **Model:** Google Gemini 2.0 Flash.
- **System Prompt (Internal Instruction):** 
  > "You are the virtual concierge for Dermaglow Aesthetic Clinic. Your tone is professional, polite, and high-end. LANGUAGE RULE: Always respond in Spanish by default. If and ONLY IF the user speaks to you in English, respond in English. Be concise and answer ONLY what the user asks."
- **Webhook Route:** Operates on `/webhook/` (trailing slash required for compatibility).
- **Availability Rule:** Reactive responses (answering user questions) must be active 24/7. The "Active Window" restrictions below apply ONLY to automated reminders and cancellations.
- **Conversation Flow:** Load `flow.json` to guide the user.
- **RAG (Retrieval-Augmented Generation):** True RAG implementation using the **Gemini File API**. Relevant files (PDF/TXT) are uploaded to Gemini and attached as file objects to the AI request for deep context awareness.

# 2. Database Models
- **`User`:** `id`, `phone_number`, `current_flow_step`, `name`, `email`.
- **`Appointment`:**
    - `user_id`, `start_time` (DateTime).
    - `status` (Enum: 'pending_payment', 'confirmed', 'cancelled').
    - `paid` (Boolean, default=False).
    - `reminder_due_at` (DateTime, nullable).
    - `cancellation_due_at` (DateTime, nullable).
- **`KnowledgeFile`:** `filename`, `gemini_uri`, `gemini_name`, `upload_date`.

# 3. Smart Scheduling Logic (The Calculator)
Create a utility function `calculate_next_business_slot(start_time, hours_delay)`:
- **Configuration:** Load start/end hours from environment variables:
    - `COMM_START_HOUR` (default: 10)
    - `COMM_END_HOUR` (default: 22)
- **Logic:** Add `hours_delay` to `start_time`.
    - If the result is **after COMM_END_HOUR**, move it to **COMM_START_HOUR** the next day.
    - If the result is **before COMM_START_HOUR**, move it to **COMM_START_HOUR** today.
- **Goal:** Ensure no proactive reminders are ever sent during the night.

# 4. Core Workflows

## A. Booking & Calendar
- **Action:** When `flow.json` triggers `book_slot`:
    1.  Check Google Calendar availability.
    2.  **Conflict Handling:** If the slot is taken, find the 2 closest available slots and return them to the AI so it can suggest them.
    3.  **Success:** Create event, set status='pending_payment', and run `calculate_next_business_slot(now, 5)` to set `reminder_due_at`.

## B. Payment Verification (The Cron Job)
Create a route `/cron/process_tasks` (to be run every 15 mins).
1.  **Send Reminders:**
    - Find appointments where `paid=False` AND `reminder_due_at <= NOW`.
    - Send: "Polite reminder: Please send $30 payment screenshot to secure your slot."
    - Clear `reminder_due_at`.
    - Set `cancellation_due_at` using `calculate_next_business_slot(now, 5)`.
2.  **Process Cancellations:**
    - Find appointments where `paid=False` AND `cancellation_due_at <= NOW`.
    - Send: "Appointment cancelled due to non-payment. Please re-book."
    - Set status='cancelled' and delete from Google Calendar.

## C. Image Handling (Proof of Payment)
- In the Twilio Webhook: If an image is received from a user with a `pending_payment` appointment:
    - Set `paid=True`.
    - Clear `reminder_due_at` and `cancellation_due_at`.
    - Reply: "Thank you. Your appointment is confirmed. 💎"

# 5. Admin Panel (Knowledge Base)
- **Route:** `/admin/upload` (Protected by Basic Auth).
- **Features:** List current files, Upload new TXT/PDF, Delete file.
- **Sync:** On upload, files are stored locally in `uploads/` AND synced via `genai.upload_file()`.
- **Delete:** Removing a file deletes it from the local database, local storage, AND the Gemini Cloud.

# 6. Google Sheets Integration (Live Dashboard)
- **Primary Function:** Acts as a real-time CRM and operations dashboard.
- **Sync Logic:** Every appointment creation, payment confirmation, or cancellation triggers a row update or append.
- **Data Columns:**
  - `Date`, `Time`, `Client Name`, `Phone Number`, `Client Notes (AI Summary)`, `Status`, `Google Event ID`.
- **AI-Driven CRM:** The "Client Notes" column is populated by an automated Gemini summary of the last 20 conversation messages, providing context to staff without reading full chat logs.
- **Implemented Features:**
    - [x] Implement AI Client Notes extraction
    - [x] Implement Visual Status Tracking (Colors)
    - [x] Implement Automatic Header Initialization
- **Visual Status Tracking:** Uses the Sheets API to highlight "PAID/CONFIRMED" rows in Green, "CANCELLED" in Red, and "PENDING" in Yellow for instant visibility.

# 7. Proposed Improvements
- **CRM Enhancement:** Implement a separate "Client Master" sheet that maintains a single row per client with their latest interest, last treatment date, and total spend.
- **One-Click Communication:** Add a column with direct `wa.me` links to open WhatsApp conversation for any entry in the spreadsheet.

# Output Requirements
- Provide `app.py`, `models.py`, `requirements.txt`, `passenger_wsgi.py`.
- **Config:** Use `.env` for all keys AND the new variables:
    - `COMM_START_HOUR=10`
    - `COMM_END_HOUR=22`

