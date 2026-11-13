"""Extracts clean text from uploaded PDF, DOCX, and text resumes."""
import io
import re
from typing import Tuple


def clean_extracted_text(text: str) -> str:
    """Normalize whitespace and remove excessive non-printable characters."""
    # Replace null bytes
    text = text.replace("\x00", "")
    # Normalize multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize non-breaking spaces
    text = text.replace("\u00a0", " ")
    return text.strip()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pymupdf."""
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text)
    doc.close()
    return clean_extracted_text("\n\n".join(pages_text))


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    import docx

    doc_stream = io.BytesIO(file_bytes)
    doc = docx.Document(doc_stream)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    
    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)

    return clean_extracted_text("\n".join(paragraphs))


def parse_resume_file(filename: str, file_bytes: bytes) -> Tuple[str, str]:
    """Parse resume by extension and return (extracted_text, detected_type)."""
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes), "pdf"
    elif lower_name.endswith(".docx"):
        return extract_text_from_docx(file_bytes), "docx"
    elif lower_name.endswith(".txt") or lower_name.endswith(".md"):
        try:
            return clean_extracted_text(file_bytes.decode("utf-8")), "text"
        except UnicodeDecodeError:
            return clean_extracted_text(file_bytes.decode("latin-1", errors="ignore")), "text"
    else:
        raise ValueError(f"Unsupported file format '{filename}'. Please upload a PDF, DOCX, TXT, or MD file.")
