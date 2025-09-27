import os
from openai import OpenAI
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get the key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ API key not found. Make sure .env file exists and has OPENAI_API_KEY.")
    exit()

client = OpenAI(api_key=api_key)

# Test request
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",   # lightweight + fast
        messages=[{"role": "user", "content": "Say hello from my Trip Planner project"}],
        max_tokens=50
    )
    print("✅ OpenAI API is working!")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("❌ Error calling API:", e)
