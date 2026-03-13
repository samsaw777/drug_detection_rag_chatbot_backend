import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import Settings


load_dotenv()
settings = Settings()

def get_llm(model: str = "gemini-2.5-flash") -> ChatGoogleGenerativeAI:
    """
    Returns a configured Gemini LLM instance.
    temperature=0 → deterministic output (no creativity needed for query analysis).
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment / .env file")

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0,
    )