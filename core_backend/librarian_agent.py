# core_backend/librarian_agent.py
import pypdf
import spacy
import re
import jdatetime
from datetime import datetime

# Load the placeholder pre-trained model as specified in the roadmap
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

def calendar_conversion_placeholder(gregorian_year: int) -> str:
    """
    Placeholder for the calendar conversion module.
    Converts a Gregorian year to a Shamsi (Jalali) year.
    """
    if not gregorian_year:
        return ""
    try:
        # We use a representative date (like June 21st) for the conversion
        g_date = datetime(gregorian_year, 6, 21)
        jalali_date = jdatetime.date.fromgregorian(date=g_date)
        return str(jalali_date.year)
    except Exception:
        return "" # Return empty string if conversion fails

def extract_metadata_from_pdf(pdf_path: str) -> dict:
    """
    Extracts Title, Author, and Year from the first page of a PDF.
    This is a 'best guess' implementation for Sprint 1 using a placeholder model.
    """
    metadata = {
        "title": "",
        "authors": [],
        "gregorian_year": "",
        "shamsi_year": ""
    }

    try:
        reader = pypdf.PdfReader(pdf_path)
        first_page_text = reader.pages[0].extract_text() or ""

        # --- Placeholder Logic ---
        # 1. Guess Title: Use the first few non-empty lines of text.
        lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]
        if lines:
            # Often the title is one or two lines, let's join them.
            metadata["title"] = " ".join(lines[:2])

        # 2. Guess Authors: Use spaCy placeholder to find PERSON entities
        if nlp:
            doc = nlp(first_page_text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    # Avoid adding very long strings that are likely not names
                    if len(ent.text.strip()) < 50:
                        metadata["authors"].append(ent.text.strip())

        # 3. Guess Year: Use regex to find a 4-digit number (likely a year)
        year_match = re.search(r'\b(19|20)\d{2}\b', first_page_text)
        if year_match:
            year = int(year_match.group(0))
            metadata["gregorian_year"] = str(year)
            metadata["shamsi_year"] = calendar_conversion_placeholder(year)

    except Exception as e:
        print(f"Error processing PDF: {e}")
        # On failure, return an empty but valid structure
        return {"title": "Error reading PDF", "authors": [], "gregorian_year": "", "shamsi_year": ""}

    return metadata