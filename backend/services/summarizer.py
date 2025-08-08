# summarizer_service.py

from models.llm_client import ask_openai_sync


def summarize_text(raw_text, model="gpt-oss-120b"):
    prompt = f"Please summarize the following:\n\n{raw_text}"
    return ask_openai_sync(prompt, model=model)
