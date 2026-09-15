import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

load_dotenv("backend/.env")

from langchain_groq import ChatGroq
from app.ai.schemas.argument_analysis_schema import ArgumentAnalysisResponse

for model in ["groq/compound", "qwen/qwen3.6-27b", "openai/gpt-oss-20b", "llama3-8b-8192"]:
    print(f"\nTesting model: {model}...", flush=True)
    try:
        llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name=model,
            temperature=0.3
        )
        chain = llm.with_structured_output(ArgumentAnalysisResponse)
        res = chain.invoke("We must invest in public transportation to reduce traffic congestion and emissions.")
        print(f"SUCCESS with {model}! Overall score: {res.argument_scoring.overall_score}")
        break
    except Exception as e:
        print(f"FAILED with {model}: {e}")
