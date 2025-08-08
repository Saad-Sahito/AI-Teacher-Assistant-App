# summarizer_service.py

from models.llm_client import ask_openai_sync


def summarize_text(raw_text, prompt_type, model="gpt-oss-120b"):
    if prompt_type == "summary":
        prompt = f"Summarize the following:\n\n{raw_text}"
    elif prompt_type == "class_notes":
        prompt = f"Make class notes from this text for one class:\n\n{raw_text}"
    return ask_openai_sync(prompt, model=model)
