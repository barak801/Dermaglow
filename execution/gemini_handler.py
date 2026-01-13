import os
import google.generativeai as genai
from datetime import datetime

class GeminiHandler:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.0-flash"
        self.model = genai.GenerativeModel(self.model_name)

    def upload_file(self, path, display_name=None):
        """
        Uploads a file to the Gemini File API.
        """
        print(f"    [Gemini] Uploading file: {path}")
        file = genai.upload_file(path=path, display_name=display_name)
        print(f"    [Gemini] File uploaded: {file.uri}")
        return file.name # This is the unique identifier needed for later

    def delete_file(self, file_name):
        """
        Deletes a file from the Gemini File API.
        """
        try:
            print(f"    [Gemini] Deleting file: {file_name}")
            genai.delete_file(file_name)
            return True
        except Exception as e:
            print(f"    [Gemini] Error deleting file {file_name}: {e}")
            return False


    def get_response(self, user_message, history, file_uris):
        """
        Generates a response using RAG and conversation history.
        """
        # Prepare context from history
        chat_history = []
        for msg in history:
            chat_history.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [msg.content]
            })

        # Prepare files for RAG
        # Note: In a real scenario, you'd want to attach these to the prompt or use File API
        # Here we assume file_uris are passed to the model
        
        # System prompt for Dermaglow
        system_instruction = (
            "You are a helpful assistant for Dermaglow Aesthetic Clinic. "
            "Use the provided knowledge base to answer questions accurately. "
            "If you don't know the answer based on the context, politely say so. "
            "Be professional and encouraging."
        )

        model_with_context = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction
        )

        chat = model_with_context.start_chat(history=chat_history)
        
        # 4. Prepare Message Parts (Text + Files)
        message_parts = [user_message]
        
        if file_uris:
            print(f"    [Gemini] Including {len(file_uris)} files in context...")
            for uri in file_uris:
                # Retrieve the file reference from Gemini
                try:
                    file_ref = genai.get_file(uri)
                    message_parts.append(file_ref)
                except Exception as e:
                    print(f"    [Gemini] Warning: Could not retrieve file {uri}: {e}")
        
        response = chat.send_message(message_parts)
        return response.text

    def summarize_conversation(self, history):
        """
        Generates a summary of the lead's interests.
        """
        summary_prompt = (
            "Based on the following conversation history, create a concise summary of the lead's profile. "
            "Include: 1. Main concerns/interest area, 2. Budget/Urgency (if mentioned), 3. Personality trait. "
            "Format: Summary | Key Interests (comma separated tags).\n\n"
        )
        for msg in history:
            summary_prompt += f"{msg.role.upper()}: {msg.content}\n"

        response = self.model.generate_content(summary_prompt)
        return response.text
