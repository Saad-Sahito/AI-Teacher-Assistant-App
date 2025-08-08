# summarizer_service.py

from models.llm_client import ask_openai_sync


def summarize_text(raw_text, prompt_type, class_grade=None, subject=None, model="gpt-oss-120b"):
    if prompt_type == "Summary":
        prompt = f"Summarize the following:\n\n{raw_text}"
    elif prompt_type == "Class Notes":
        prompt = f"Make class teaching notes from this text for one class:\n\n{raw_text}"
    elif prompt_type == "Lesson Plan":
        prompt = f"""
You are an experienced teacher. Create a structured lesson plan for a {class_grade} {subject} class from the following content from the following content for a single 40-minute class. Focus on engaging students and achieving clear learning outcomes.

Use the following format:
1. **Topic**: (Title of the lesson)
2. **Grade/Class Level**: (Estimate based on content)
3. **Learning Objectives**: (3-4 clear "Students will be able to..." statements)
4. **Materials Needed**: (List of any required materials)
5. **Lesson Duration**: (Total and per section)
6. **Lesson Activities**:
   - Introduction (5 mins): 
   - Main Teaching (20 mins):
   - Practice Activity (10 mins):
   - Wrap-up/Exit Ticket (5 mins):
7. **Assessment Method**: (How the teacher will evaluate understanding)
8. **Homework (Optional)**: (If relevant)

Text to base this on:
{raw_text}
"""

    return ask_openai_sync(prompt=prompt, model=model)
