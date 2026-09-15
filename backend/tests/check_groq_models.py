import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

load_dotenv("backend/.env")
key = os.getenv("GROQ_API_KEY")

from groq import Groq

client = Groq(api_key=key)
try:
    models = client.models.list()
    print("Available Groq Models for this API Key:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"Error querying Groq models: {e}")
