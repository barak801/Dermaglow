import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def test_vision(file_path, expected_amount):
    print(f"Testing Gemini Vision with: {file_path}")
    sample_file = genai.upload_file(path=file_path, display_name="Test Payment Proof")
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    Analyze this screenshot to verify a deposit payment for a medical aesthetic clinic.
    Target Amount: {expected_amount}
    
    Tasks:
    1. Identify if this is a payment receipt/confirmation (Transferencia, Nequi, Daviplata, or Bank receipt).
    2. Extract the TOTAL AMOUNT paid.
    3. Check if the amount matches {expected_amount}.
    
    Return ONLY a JSON object:
    {{
      "is_receipt": bool,
      "amount_matches": bool,
      "amount_found": "string value found",
      "currency": "string currency",
      "reason": "brief explanation"
    }}
    """
    
    result = model.generate_content([sample_file, prompt])
    res_text = result.text.strip()
    
    if res_text.startswith('```json'):
        res_text = res_text.split('```json')[1].split('```')[0].strip()
    elif res_text.startswith('```'):
        res_text = res_text.split('```')[1].split('```')[0].strip()
        
    print("Gemini Response:")
    print(res_text)
    return json.loads(res_text)

if __name__ == "__main__":
    # Path to the generated mock image
    IMAGE_PATH = "/home/barak/.gemini/antigravity/brain/e28152c9-7000-4393-8275-f3b8868e7b0e/mock_payment_30_dollars_1768618983680.png"
    if os.path.exists(IMAGE_PATH):
        test_vision(IMAGE_PATH, "$30")
    else:
        print(f"Image not found at {IMAGE_PATH}")
