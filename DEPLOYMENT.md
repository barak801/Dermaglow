# Deployment & Setup Guide - Dermaglow AI Concierge

This guide provides step-by-step instructions to set up and run the Dermaglow AI Concierge on your own environment.

## 1. Prerequisites
- Python 3.10 or higher.
- A Twilio Account (for WhatsApp integration).
- A Google Cloud Project (for Calendar, Sheets, and Gemini APIs).
- A Google Gemini API Key.

## 2. Environment Configuration
1. Clone this repository.
2. Copy the `.env.example` file to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
3. Fill in the values in `.env` with your specific credentials.

## 3. Google API Configuration
### Google Cloud Console Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the following APIs:
   - Google Calendar API
   - Google Sheets API
   - Generative Language API (for Gemini)
3. Create a **Service Account**:
   - Go to "IAM & Admin" > "Service Accounts".
   - Create a service account and download the **JSON Key**.
   - Rename the downloaded file to `service_account.json` and place it in the project root.
4. **Share Resources**:
   - Share your Google Calendar with the service account email.
   - Share your Google Sheet (Editor access) with the service account email.

### Gemini API Key
- Obtain your Gemini API Key from [Google AI Studio](https://aistudio.google.com/) and add it to `GEMINI_API_KEY` in `.env`.

## 4. Twilio Integration
1. Log in to your [Twilio Console](https://www.twilio.com/console).
2. Configure your WhatsApp Sandbox or Production Number.
3. Set the Webhook URL for incoming messages to:
   `https://your-domain.com/webhook/` (Make sure to include the trailing slash).

## 5. Installation & Execution
1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Initialize the local database:
   ```bash
   python3 -c "from app import db; db.create_all()"
   ```
3. Run the application:
   ```bash
   python3 app.py
   ```

## 6. Admin Panel
- Access the clinical dashboard at `https://your-domain.com/admin/upload`.
- Default credentials are set in your `.env` file (`ADMIN_USERNAME` and `ADMIN_PASSWORD`).
