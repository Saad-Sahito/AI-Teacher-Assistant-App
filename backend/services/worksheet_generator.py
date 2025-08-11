from models.llm_client import ask_openai_sync
import os

from docx import Document
from io import BytesIO
import json
import re


def generate_worksheet(raw_text, num_questions, worksheet_type="Mixed", class_grade=None, subject=None):
    prompt = f"""
You are a worksheet generator AI. Generate {num_questions} questions in {worksheet_type} question answer format, from the following study material, for a {subject} {class_grade} class. 
Output questions and answers key in the end.

Study Material:
{raw_text}
"""

    response = ask_openai_sync(prompt)
    #print(response)
    #temp = extract_quiz_json(response)
    #print (temp)
    return response