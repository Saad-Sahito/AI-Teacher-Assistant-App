import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader

from services.quiz_gen import generate_quiz_from_text, generate_quiz_docx
from services.flashcard_gen import generate_flashcards_from_path
from services.summarizer import summarize_text
from services.chapter_splitter import main_split

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet


# PDF generation function
def generate_pdf(summary_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    flowables = []

    for para in summary_text.split("\n\n"):
        flowables.append(Paragraph(para.strip(), styles["Normal"]))
        flowables.append(Spacer(1, 12))

    doc.build(flowables)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf




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

# if feature == "📄 Flashcards":
#     uploaded_file = st.file_uploader("Upload a PDF to generate flashcards", type=["pdf"])
#     if uploaded_file and st.button("Generate Flashcards"):
#         # Save uploaded file to a temporary file
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             tmp_file.write(uploaded_file.read())
#             temp_pdf_path = tmp_file.name

#         try:
#             flashcards = generate_flashcards_from_path(temp_pdf_path)

#             for i, (q, a) in enumerate(flashcards.items()):
#                 st.markdown(f"**Q{i+1}: {q}**")
#                 st.markdown(f"🔹 {a}")
#                 st.markdown("---")
#         except Exception as e:
#             st.error(str(e))

if feature == "📝 Quiz Generator":
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

    class_grade_options = ["grade 1","grade 2","grade 3","grade 4","grade 5","grade 6","grade 7","grade 8","grade 9","grade 10","grade 11","grade 12","1st year college","2nd year college","3rd year college","4th year college"]
    class_grade = st.selectbox("Choose class grade: (Consider Intermediate/A-Level to be grade 11/12)", class_grade_options)

    subject_options = ["Science", "Mathematics", "History", "Geography", "English Language", "Physics", "Chemistry", "Islamic Studies"]
    subject = st.selectbox("Choose class subject:", subject_options)
    
    prompt_type_options = ["Summary", "Class Notes", "Lesson Plan"]
    prompt_type = st.selectbox("Choose a summary type:", prompt_type_options)

    st.write(f"You selected: {prompt_type}")

    raw_text = st.text_area("✏️ Paste or edit the text to summarize", value=default_text, height=300)

    if st.button("Summarize") and raw_text.strip():
        with st.spinner("Summarizing..."):
            try:
                summary = summarize_text(
                    prompt_type=prompt_type,
                    raw_text=raw_text,
                    class_grade=class_grade,
                    subject=subject
                )
                st.success("📝 Summary:")
                st.markdown(summary)

                # Generate PDF on button click
                if st.button("Convert to PDF") and summary:
                    pdf_bytes = generate_pdf(summary)

                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_bytes,
                        file_name="summary.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# elif feature == "📖 Split Chapters":
#     uploaded_file = st.file_uploader("Upload a PDF to split into chapters", type=["pdf"])
#     if uploaded_file and st.button("Split Chapters"):
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             tmp_file.write(uploaded_file.read())
#             temp_pdf_path = tmp_file.name

#         # Create main output folder inside ../assets
#         base_output_dir = os.path.join("..", "assets", "chapters_output")
#         os.makedirs(base_output_dir, exist_ok=True)

#         # Create subfolder using uploaded file name (without extension)
#         file_name = os.path.splitext(uploaded_file.name)[0]
#         output_dir = os.path.join(base_output_dir, file_name)
#         os.makedirs(output_dir, exist_ok=True)

#         main_split(temp_pdf_path, output_dir)

#         for ch_filename in sorted(os.listdir(output_dir)):
#             ch_path = os.path.join(output_dir, ch_filename)
#             st.markdown(f"#### {ch_filename}")
#             with open(ch_path, "rb") as f:
#                 st.download_button(f"📥 Download {ch_filename}", f, file_name=ch_filename)




