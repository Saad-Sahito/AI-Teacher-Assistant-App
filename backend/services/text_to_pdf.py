from models.llm_client import ask_openai_sync




def convert_text_to_pdf(raw_text, model="gpt-oss-120b"):
    prompt = f"""
    You are a teacher preparing educational content to be turned into a printable PDF. Take the following unformatted text and reformat it using Markdown so it’s clean and readable in a document.

    Use:
    - `#` for main headings
    - `##` for subheadings
    - Bullet points for lists
    - Numbered lists when needed
    - Bold text for key terms or definitions
    - Keep paragraphs clean and separated

    Text:
    \"\"\"{raw_text}\"\"\"
    """
    return ask_openai_sync(prompt=prompt, model=model)
