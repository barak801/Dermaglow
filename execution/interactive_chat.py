import requests
import time
import sys

def interactive_chat():
    print("\n--- 💎 DERMAGLOW CLINIC INTERACTIVE TEST 💎 ---")
    # Use a fixed phone number for the session or get it from args
    phone_number = sys.argv[1] if len(sys.argv) > 1 else "whatsapp:+1234567890"
    print(f"Chatting as: {phone_number}")
    print("-----------------------------------------------\n")
    
    while True:
        try:
            user_input = input(f"\nYou ({phone_number}): ")
            if user_input.lower() in ['quit', 'exit']:
                print("Exiting chat. Bye! 👋")
                break
                
            if not user_input.strip():
                continue
                
            payload = {
                "From": phone_number,
                "Body": user_input,
                "NumMedia": "0"
            }

            if user_input.startswith("/image "):
                image_url = user_input.replace("/image ", "").strip()
                payload["NumMedia"] = "1"
                payload["MediaUrl0"] = image_url
                payload["Body"] = "" # Often body is empty on image send
                print(f"--- Simulating Image Upload: {image_url} ---")
            
            # Show "Jesica is typing..." delay effect
            sys.stdout.write("Jesica is typing...")
            sys.stdout.flush()
            
            start_time = time.time()
            response = requests.post("http://localhost:5000/webhook/", data=payload)
            elapsed = time.time() - start_time
            
            # Clear the "typing" line
            sys.stdout.write("\r" + " " * 20 + "\r")
            
            if response.status_code == 200:
                # Extract simple body from Twilio XML without external parsing lib if possible, 
                # or just look for <Body> tags
                text = response.text
                if "<Body>" in text and "</Body>" in text:
                    body_content = text.split("<Body>")[1].split("</Body>")[0]
                    # Unescape HTML entities if needed (basic ones)
                    body_content = body_content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#243;", "ó").replace("&#233;", "é").replace("&#225;", "á").replace("&#237;", "í").replace("&#250;", "ú").replace("&#241;", "ñ").replace("&#191;", "¿")
                    print(f"Jesica 👩‍⚕️ ({elapsed:.1f}s):\n{body_content}")
                else:
                    print(f"Server Response:\n{text}")
            else:
                print(f"Error ({response.status_code}): {response.text}")
                
        except KeyboardInterrupt:
            print("\nExiting chat. Bye! 👋")
            break
        except Exception as e:
            print(f"\nConnection Error: {e}")
            break

if __name__ == "__main__":
    interactive_chat()
