
import os
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found in .env!")

# Initialize Gemini
client = genai.Client(api_key=api_key)

# Send test prompt
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Explain what a research paper analyzer does."
)

print("\nGemini Response:\n")
print(response.text)
