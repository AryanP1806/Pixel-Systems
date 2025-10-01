import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

print("Loaded API Key:", api_key)


genai.configure(api_key=api_key)

try:
    models = genai.list_models()
    for m in models:
        print("Available model:", m.name)
except Exception as e:
    print("Error listing models:", e)

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    exit()

# Configure Gemini
genai.configure(api_key=api_key)

# Use a correct model name
model = genai.GenerativeModel("gemini-2.5-pro")

# Start chat
chat_session = model.start_chat(history=[])

def run_chatbot():
    print("🤖 Gemini Chatbot Ready! (Type 'quit' to exit)\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("👋 Goodbye!")
            break

        if not user_input:
            print("Please type something.")
            continue

        try:
            response = chat_session.send_message(user_input)
            print("Gemini:", response.text)
        except Exception as e:
            print(f"❌ Error: {e}")
            break

if __name__ == "__main__":
    run_chatbot()
