from pypdf import PdfReader
from collections import Counter


def extract_text_from_pdf(file) -> str:
    try:
        reader = PdfReader(file)
    except Exception:
        return ""

    page_texts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            page_texts.append(text)

    if not page_texts:
        return ""

    # Detect repeated lines (headers/footers)
    all_lines = []
    for text in page_texts:
        all_lines.extend(text.splitlines())

    line_counts = Counter(all_lines)
    repeated_lines = {
        line for line, count in line_counts.items() if count > 2 and len(line) < 100
    }

    cleaned_pages = []
    for text in page_texts:
        lines = [
            line for line in text.splitlines()
            if line not in repeated_lines
        ]
        cleaned_pages.append("\n".join(lines))

    return "\n".join(cleaned_pages)
