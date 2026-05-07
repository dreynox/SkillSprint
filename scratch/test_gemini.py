import os
import google.generativeai as genAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No API key found in .env")
    exit(1)

genAI.configure(api_key=api_key)

print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}")

try:
    print("\n--- Available Models ---")
    for m in genAI.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
    
    print("\n--- Testing gemini-1.5-flash ---")
    model = genAI.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Hello, are you there?")
    print(f"Response: {response.text}")

except Exception as e:
    print(f"\nERROR: {str(e)}")
