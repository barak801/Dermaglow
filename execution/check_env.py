import os
from dotenv import load_dotenv

def check_env():
    load_dotenv()
    
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "GEMINI_API_KEY",
        "DATABASE_URL"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please check your .env file.")
        return False
    else:
        print("✅ All required environment variables are set.")
        return True

if __name__ == "__main__":
    check_env()
