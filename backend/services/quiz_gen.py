from models.llm_client import ask_openai_sync
import os

from docx import Document
from io import BytesIO
import json
import re


def generate_quiz_from_text(text, num_questions=5):
    prompt = f"""
You are a quiz generator AI. Generate {num_questions} multiple choice questions from the following study material. 
Each question should have 1 correct option and 3 incorrect options.
Return in this JSON format:
[
  {{
    "question": "What is ...?",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "answer": "A"
  }},
  ...
]

Study Material:
{text}
"""

    response = ask_openai_sync(prompt)
    #print(response)
    temp = extract_quiz_json(response)
    #print (temp)
    return temp
    

def extract_quiz_json(content_str):
    try:
        content = content_str.strip()

        if content.startswith('['):
            return json.loads(content)

        json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)

        raise ValueError("No valid JSON array found in input.")

    except Exception as e:
        return [{
            "question": "Error parsing quiz.",
            "options": [],
            "answer": f"{type(e).__name__}: {str(e)}"
        }]



def generate_quiz_docx(quiz_data, title="Generated Quiz"):
    doc = Document()
    doc.add_heading(title, level=1)

    for idx, q in enumerate(quiz_data, 1):
        doc.add_paragraph(f"Q{idx}: {q['question']}", style='List Number')
        for opt in q['options']:
            doc.add_paragraph(opt, style='List Bullet')
        doc.add_paragraph(f"✅ Answer: {q['answer']}\n")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

