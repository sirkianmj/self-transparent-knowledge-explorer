# core_backend/librarian_agent.py
import pypdf
import spacy
import re
import jdatetime
from datetime import datetime
import os
import sqlite3
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# --- DATABASE AND MODEL INITIALIZATION ---
DB_NAME = "knowledge_base.db"

# Load the placeholder NLP model for author extraction
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None

# Load the embedding model. This will download it the first time it's run.
# 'all-MiniLM-L6-v2' is a small, fast, and effective model.
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# NEW, PERSISTENT CODE
# Initialize the vector database client to save data to disk
chroma_client = chromadb.PersistentClient(path="local_chroma") # This will save files in a 'local_chroma' directory
# Create or get the "local_library" collection.
local_collection = chroma_client.get_or_create_collection(name="local_library")
# --- SPRINT 1 FUNCTION (No changes needed) ---
def extract_metadata_from_pdf(pdf_path: str) -> dict:
    # ... (This function remains exactly the same as in Sprint 1) ...
    metadata = {
        "title": "", "authors": [], "gregorian_year": "", "shamsi_year": ""
    }
    try:
        reader = pypdf.PdfReader(pdf_path)
        first_page_text = reader.pages[0].extract_text() or ""
        lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]
        if lines:
            metadata["title"] = " ".join(lines[:2])
        if nlp:
            doc = nlp(first_page_text)
            for ent in doc.ents:
                if ent.label_ == "PERSON" and len(ent.text.strip()) < 50:
                    metadata["authors"].append(ent.text.strip())
        year_match = re.search(r'\b(19|20)\d{2}\b', first_page_text)
        if year_match:
            year = int(year_match.group(0))
            metadata["gregorian_year"] = str(year)
            # ... (calendar conversion logic can be added back if needed) ...
    except Exception as e:
        print(f"Error during initial extraction: {e}")
    return metadata

# --- SPRINT 2 NEW FUNCTIONS ---
def generate_standardized_filename(title: str, year: int, authors: list) -> str:
    """Creates a clean, standardized filename."""
    author_surname = authors[0].split()[-1] if authors else "UnknownAuthor"
    clean_title = "".join(c for c in title if c.isalnum() or c in " _-").rstrip()
    short_title = clean_title.replace(" ", "_")[:30]
    return f"{year}_{author_surname}_{short_title}.pdf"

def finalize_ingestion_in_local_library(
    temp_pdf_path: str,
    title: str,
    authors: list,
    gregorian_year: int
):
    """
    The core processing pipeline for saving a document to the local library.
    """
    # 1. Generate new filename and permanent path
    library_dir = "local_library_storage"
    os.makedirs(library_dir, exist_ok=True)
    new_filename = generate_standardized_filename(title, gregorian_year, authors)
    permanent_path = os.path.join(library_dir, new_filename)
    
    # 2. Move the file
    os.rename(temp_pdf_path, permanent_path)

    # 3. Save metadata to SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO local_documents (title, authors, publication_year, original_filename, storage_filename, language) VALUES (?, ?, ?, ?, ?, ?)",
        (title, ", ".join(authors), gregorian_year, os.path.basename(temp_pdf_path), new_filename, "en") # Placeholder for language
    )
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # NEW, ROBUST CODE
    # 4. Read text, chunk it, and create embeddings
    reader = pypdf.PdfReader(permanent_path)
    # Ensure full_text is not None
    full_text = "".join(page.extract_text() or "" for page in reader.pages)

    # --- GUARD CLAUSE ---
    # If no text was extracted, we cannot proceed with embedding.
    # We'll still keep the document in the SQLite DB, but it won't be searchable.
    if not full_text.strip():
        print(f"WARNING: No text could be extracted from {new_filename}. Skipping vectorization.")
        return new_filename # Exit the function early

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_text(full_text)

    # --- SECOND GUARD CLAUSE ---
    # If there are chunks, create embeddings
    if chunks:
        embeddings = embedding_model.encode(chunks)

    # 5. Save chunks and embeddings to ChromaDB
    chunk_ids = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks))]
    local_collection.add(
        embeddings=embeddings.tolist(),
        documents=chunks,
        metadatas=[{"source_doc_id": doc_id} for _ in chunks],
        ids=chunk_ids
    )