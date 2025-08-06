import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader

from services.quiz_gen import generate_quiz_from_text, generate_quiz_docx
from services.flashcard_gen import generate_flashcards_from_path
from services.summarizer import summarize_text
from services.chapter_splitter import main_split








def display_quiz(quiz):
    for idx, q in enumerate(quiz, start=1):
        st.markdown(f"### Q{idx}: {q['question']}")
        
        # Display options
        for option in q["options"]:
            st.markdown(f"- {option}")

        # Display correct answer
        try:
            answer_letter = q["answer"].strip().upper()
            if len(answer_letter) == 1 and 'A' <= answer_letter <= 'Z':
                answer_index = ord(answer_letter) - ord('A')
                if 0 <= answer_index < len(q['options']):
                    correct_option_text = q['options'][answer_index]
                    st.success(f"✅ Correct Answer: {correct_option_text}")
                else:
                    st.warning(f"⚠️ Invalid answer index: {answer_index}")
            else:
                st.success(f"✅ Correct Answer: {q['answer']}")
        except Exception as e:
            st.error(f"❌ Error showing answer: {str(e)}")






st.set_page_config(page_title="AI App", layout="wide")
st.title("🧠 AI App")

# Sidebar navigation
feature = st.sidebar.radio("Choose a feature", [
    "📄 Flashcards",
    "📝 Quiz Generator",
    "📝 Summarizer",
    "📖 Split Chapters"
])

if feature == "📄 Flashcards":
    uploaded_file = st.file_uploader("Upload a PDF to generate flashcards", type=["pdf"])
    if uploaded_file and st.button("Generate Flashcards"):
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_pdf_path = tmp_file.name

        try:
            flashcards = generate_flashcards_from_path(temp_pdf_path)

            for i, (q, a) in enumerate(flashcards.items()):
                st.markdown(f"**Q{i+1}: {q}**")
                st.markdown(f"🔹 {a}")
                st.markdown("---")
        except Exception as e:
            st.error(str(e))

elif feature == "📝 Quiz Generator":
    st.title("📝 Quiz Generator")

    uploaded_pdf = st.file_uploader("📄 Upload a PDF (optional)", type=["pdf"])
    default_text = ""

    if uploaded_pdf:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_pdf.read())
            temp_pdf_path = tmp_file.name

        reader = PdfReader(temp_pdf_path)
        for page in reader.pages:
            default_text += page.extract_text() or ""
        st.success("✅ PDF text extracted!")

    text_input = st.text_area("✏️ Paste or edit content for quiz generation:", value=default_text, height=300)

    num_questions = st.number_input("🔢 Number of questions", min_value=1, max_value=200, value=5, step=1)

    if st.button("Generate Quiz") and text_input.strip():
        with st.spinner("Generating quiz..."):
            quiz = generate_quiz_from_text(text_input, num_questions=num_questions)
            st.session_state.quiz_data = quiz  # store in session state
            display_quiz(quiz)

    # Check if quiz is stored
    if "quiz_data" in st.session_state:
        if st.button("Download Quiz as Word File"):
            docx_file = generate_quiz_docx(st.session_state.quiz_data, title="Quiz from AI")
            st.download_button(
                label="📥 Download Word File",
                data=docx_file,
                file_name="ai_generated_quiz.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )




elif feature == "📝 Summarizer":
    st.title("Text Summarizer")

    uploaded_pdf = st.file_uploader("📄 Or upload a PDF to extract text", type=["pdf"])

    default_text = ""

    if uploaded_pdf:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_pdf.read())
            temp_pdf_path = tmp_file.name


        try:
            reader = PdfReader(temp_pdf_path)
            extracted_text = ""
            for page in reader.pages:
                extracted_text += page.extract_text() or ""
            default_text = extracted_text.strip()
            st.success("✅ Text extracted from PDF! You can edit it below.")
        except Exception as e:
            st.error(f"❌ Failed to extract text: {str(e)}")

    user_input = st.text_area("✏️ Paste or edit the text to summarize", value=default_text, height=300)

    if st.button("Summarize") and user_input.strip():
        with st.spinner("Summarizing..."):
            try:
                summary = summarize_text(user_input)
                st.success("📝 Summary:")
                st.markdown(summary)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")



elif feature == "📖 Split Chapters":
    uploaded_file = st.file_uploader("Upload a PDF to split into chapters", type=["pdf"])
    if uploaded_file and st.button("Split Chapters"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_pdf_path = tmp_file.name

        # Create main output folder
        base_output_dir = "chapters_output"
        os.makedirs(base_output_dir, exist_ok=True)

        # Create subfolder using uploaded file name (without extension)
        file_name = os.path.splitext(uploaded_file.name)[0]
        output_dir = os.path.join(base_output_dir, file_name)
        os.makedirs(output_dir, exist_ok=True)

        main_split(temp_pdf_path, output_dir)

        #if os.path.exists(chapter_folder):
        for ch_filename in sorted(os.listdir(output_dir)):
            ch_path = os.path.join(output_dir, ch_filename)
            st.markdown(f"#### {ch_filename}")
            with open(ch_path, "rb") as f:
                st.download_button(f"📥 Download {ch_filename}", f, file_name=ch_filename)



