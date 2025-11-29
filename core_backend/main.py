# core_backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import shutil
import os
from librarian_agent import extract_metadata_from_pdf, finalize_ingestion_in_local_library

app = FastAPI(title="Self-Transparent Knowledge Explorer API")

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# --- Endpoint from Sprint 1 ---
@app.post("/library/ingest/interactive_start")
async def start_interactive_ingestion(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    temp_file_path = os.path.join(TEMP_DIR, file.filename)
    
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    extracted_data = extract_metadata_from_pdf(temp_file_path)
    return extracted_data

# --- New Endpoint and Logic for Sprint 2 ---
class FinalIngestionRequest(BaseModel):
    original_filename: str
    title: str
    authors: List[str]
    gregorian_year: int

# RESTORE THIS CODE in main.py
@app.post("/library/ingest/interactive_confirm")
async def confirm_interactive_ingestion(request: FinalIngestionRequest):
    """
    Receives final metadata, triggers the core processing pipeline, and
    saves the document to the local library.
    """
    temp_file_path = os.path.join(TEMP_DIR, request.original_filename)
    if not os.path.exists(temp_file_path):
        raise HTTPException(status_code=404, detail="Original file not found. Please try uploading again.")

    try:
        new_filename = finalize_ingestion_in_local_library(
            temp_pdf_path=temp_file_path,
            title=request.title,
            authors=request.authors,
            gregorian_year=request.gregorian_year
        )
        return {"status": "ingested", "new_filename": new_filename}
    except Exception as e:
        # Clean up the temp file on failure
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"An error occurred during finalization: {str(e)}")