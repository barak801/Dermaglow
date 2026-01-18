import os
from dotenv import load_dotenv
from utils import get_gemini_rag_response

def test_gemini():
    load_dotenv()
    print(f"API KEY prefix: {os.getenv('GEMINI_API_KEY')[:5] if os.getenv('GEMINI_API_KEY') else 'None'}")
    response = get_gemini_rag_response("Hi, how are you?")
    print(f"Response: {response}")

if __name__ == "__main__":
    test_gemini()
