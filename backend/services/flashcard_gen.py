# flashcard_service.py

import fitz  # PyMuPDF
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.llm_client import count_tokens, ask_openai_sync


def generate_flashcards_from_path(input_path, model="o4-mini"):
    # Normalize input to list of PDF paths
    if isinstance(input_path, list):
        pdf_paths = input_path
    elif os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
        pdf_paths = [input_path]
    elif os.path.isdir(input_path):
        pdf_paths = [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(".pdf")
        ]
        if not pdf_paths:
            raise ValueError(f"No PDF files found in folder: {input_path}")
    else:
        raise ValueError(f"Invalid input path: {input_path}")

    flashcards_combined = {}

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {
            executor.submit(generate_flashcards_from_pdf, path, model): path
            for path in pdf_paths
        }

        for future in as_completed(futures):
            path = futures[future]
            try:
                flashcards = future.result()
                flashcards_combined.update(flashcards)
            except Exception as e:
                raise RuntimeError(f"❌ Failed for {os.path.basename(path)}: {e}")

    return flashcards_combined


def generate_flashcards_from_pdf(pdf_path, model="o4-mini"):
    doc = fitz.open(pdf_path)
    full_text = "\n".join([page.get_text() for page in doc])

    MAX_INPUT_TOKENS = 100_000
    lines = full_text.splitlines()
    selected_lines = []
    total_tokens = 0

    for line in lines:
        tokens = count_tokens(line, model)
        if total_tokens + tokens > MAX_INPUT_TOKENS:
            break
        selected_lines.append(line)
        total_tokens += tokens

    limited_text = "\n".join(selected_lines)

    prompt = (
        "You are an expert flashcard generator.\n"
        "Create a dictionary of flashcards from the following text.\n"
        "Each key should be a concise question or term. Each value should be the answer or explanation.\n"
        "Return ONLY valid JSON (no markdown, no explanation).\n\n"
        f"Text:\n{limited_text}"
    )

    output = ask_openai_sync(prompt, model=model)

    try:
        flashcards = json.loads(output)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON output from LLM for: {os.path.basename(pdf_path)}")

    if not isinstance(flashcards, dict):
        raise ValueError(f"Output is not a dictionary for: {os.path.basename(pdf_path)}")

    return flashcards
