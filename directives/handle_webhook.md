# SOP: Handling Incoming Webhooks

This directive outlines the process for handling messages from Twilio (WhatsApp, Messenger, Instagram).

## Process Flow
1. **Security Verification**:
   - Check `X-Twilio-Signature`.
   - Validate using `twilio.request_validator`.
2. **Conversation Lookup**:
   - Identify user via `From` ID.
   - Fetch last 11 messages from SQLite (10 for context + 1 incoming).
3. **Summarization Trigger**:
   - If `message_count >= 20` or `idle_time > 30 mins`.
   - Call Gemini to summarize and update `LeadSummaries`.
   - Reset `message_count`.
4. **RAG Response**:
   - Retrieve Knowledge Base `file_uris`.
   - Send current message + history + KB context to Gemini.
5. **Storage**:
   - Save user and agent messages to `Messages` table.
   - Update `last_interaction` timestamp.
