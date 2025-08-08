import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
import os
import re
import json
from models.llm_client import ask_llama3_stream_false, ask_openai_sync


def get_visible_page_numbers(pdf_path):
    doc = fitz.open(pdf_path)
    page_number_map = {}
    for i, page in enumerate(doc):
        text = page.get_text("text")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        candidates = lines[:3] + lines[-3:]
        for line in candidates:
            match = re.search(r"(\d+)", line)
            if match:
                visible_page = int(match.group(1))
                if visible_page not in page_number_map:
                    page_number_map[visible_page] = i
                break
    return page_number_map


def map_chapters_to_internal_indices(chapters, visible_to_internal):
    internal_chapters = []
    for chapter in chapters:
        visible_page = chapter["page"]
        internal_page = visible_to_internal.get(visible_page)
        if internal_page is not None:
            internal_chapters.append({
                "title": chapter["title"],
                "page": internal_page
            })
    return internal_chapters


def interpolate_visible_to_internal_map(visible_to_internal, max_interpolation_range=100):
    """Fills in missing visible page numbers by linear interpolation between known ones,
    with safety checks to avoid large memory usage."""
    
    known = sorted(visible_to_internal.items())
    full_map = {}

    for i in range(len(known) - 1):
        vis1, int1 = known[i]
        vis2, int2 = known[i + 1]
        delta = vis2 - vis1

        if delta > max_interpolation_range:
            print(f"⚠️ Skipping interpolation: visible page range too large ({vis1} → {vis2})")
            continue

        step = (int2 - int1) / delta
        print(f"🔄 Interpolating: visible {vis1}-{vis2}, internal {int1}-{int2}, step={step:.2f}")
        
        for v in range(vis1, vis2):
            full_map[v] = round(int1 + step * (v - vis1))

    # Add the last known page
    full_map[known[-1][0]] = known[-1][1]

    return full_map


def split_pdf_by_chapter_list(pdf_path, chapters, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    for i, chap in enumerate(chapters):
        start = chap["page"]
        end = chapters[i + 1]["page"] if i + 1 < len(chapters) else total_pages

        writer = PdfWriter()
        for p in range(start, end):
            writer.add_page(reader.pages[p])

        safe_title = re.sub(r"[^\w\-_. ]", "_", chap["title"])[:50]
        out_path = os.path.join(output_dir, f"{i+1:02d}_{safe_title}.pdf")

        with open(out_path, "wb") as f:
            writer.write(f)

        print(f"✅ Saved: {out_path}")


def extract_chapters_from_index_with_llm(pdf_path, model="gpt-oss-120b", max_pages=10):
    doc = fitz.open(pdf_path)
    index_texts = []
    for i in range(min(max_pages, len(doc))):
        page_text = doc[i].get_text("text")
        if "contents" in page_text.lower():
            index_texts.append(page_text)
            if i + 1 < len(doc):
                next_text = doc[i + 1].get_text("text")
                if len(next_text.strip()) > 100:
                    index_texts.append(next_text)
            break

    if not index_texts:
        print("⚠️ No Table of Contents found.")
        return {}

    combined_text = "\n\n".join(index_texts)
    prompt = f"""
You are a document parser. Extract a list of major chapters and their corresponding page numbers from the following textbook index or table of contents.

Output the result as a valid Python dictionary in the format:
{{
    "Chapter Number: Name": page_number,
    ...
}}

Rules:
- Only extract top-level chapters or major sections (ignore subheadings)
- If a chapter is numbered (like "1. Introduction" or "Chapter 1 - Basics"), clean the title but preserve the number
- The page number must be a number (integer) from the right side of each entry
- Do not include sections like "Preface", "About the Author", or "Index"

Text sample:
----------------
{combined_text[:8000]}
----------------
"""
    response = ask_openai_sync(prompt.strip(), model=model)
    match = re.search(r"\{[\s\S]+?\}", response)
    if not match:
        print("❌ Could not extract dictionary from LLM response.")
        print(response)
        return {}

    dict_str = match.group(0)
    cleaned_lines = []
    for line in dict_str.splitlines():
        match = re.match(r'^(\s*"[^"]+"\s*:\s*)(\d+)(\s*\([^)]+\))?\s*,?\s*$', line)
        if match:
            cleaned_lines.append(f"{match.group(1)}{match.group(2)},")
        else:
            cleaned_lines.append(line)
    cleaned_dict_str = "\n".join(cleaned_lines)

    try:
        chapter_dict = eval(cleaned_dict_str)
        return chapter_dict if isinstance(chapter_dict, dict) else {}
    except Exception as e:
        print(f"❌ Failed to parse LLM output: {e}")
        print(cleaned_dict_str)
        return {}


def remove_duplicate_page_numbers(chapter_dict):
    seen = {}
    for title, page in chapter_dict.items():
        seen[page] = title
    return {title: page for page, title in seen.items()}


def main_split(pdf_path, output_dir, chapter_dict=None, visible_to_internal_map=None):
    print("🔍 Getting chapter list...")

    if chapter_dict is None:
        chapter_dict = extract_chapters_from_index_with_llm(pdf_path)
        print(chapter_dict)
        if not chapter_dict:
            print("❌ No chapters detected. Exiting.")
            return [], {}

    chapter_dict = remove_duplicate_page_numbers(chapter_dict)
    chapters = [{"title": t, "page": int(p)} for t, p in chapter_dict.items()]
    chapters.sort(key=lambda x: x["page"])

    print("📄 Mapping visible → internal page numbers...")

    # Use provided map or regenerate
    if visible_to_internal_map is None:
        visible_to_internal_map = get_visible_page_numbers(pdf_path)
        visible_to_internal_map = interpolate_visible_to_internal_map(visible_to_internal_map)


    internal_chapters = map_chapters_to_internal_indices(chapters, visible_to_internal_map)

    if not internal_chapters:
        print("❌ Could not map any chapter pages. Exiting.")
        return [], {}

    print(f"✂️ Splitting PDF into {len(internal_chapters)} chapters...")
    split_pdf_by_chapter_list(pdf_path, internal_chapters, output_dir)
    print("✅ All chapters split and saved.")

    return
