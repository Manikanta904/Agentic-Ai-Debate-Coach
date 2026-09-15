"""
LLM Configuration

Purpose:
    Initializes and configures the Large Language Model (LLM) used by the
    AI Debate Coach.

Responsibilities:
    - Configure LLM connection (Groq or Ollama).
    - Define model inference parameters (temperature, max_completion_tokens).
    - Export a reusable LLM instance.
"""

from app.core.config import settings

if settings.LLM_PROVIDER == "groq" and settings.GROQ_API_KEY:

    from langchain_groq import ChatGroq

    llm = ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

else:

    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
        num_predict=settings.LLM_MAX_TOKENS,
    )
