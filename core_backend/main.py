# core_backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
import os
from librarian_agent import extract_metadata_from_pdf

app = FastAPI(title="Self-Transparent Knowledge Explorer API")

# Create a temporary directory for file uploads
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/library/ingest/interactive_start")
async def start_interactive_ingestion(file: UploadFile = File(...)):
    """
    Receives a PDF, saves it temporarily, and triggers the Librarian
    agent's metadata extraction.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are accepted.")

    temp_file_path = os.path.join(TEMP_DIR, file.filename)

    try:
        # Save the uploaded file to the temporary location
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the file with the Librarian Agent
        extracted_data = extract_metadata_from_pdf(temp_file_path)

        return extracted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during file processing: {e}")
    finally:
        # Clean up: remove the temporary file after processing
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)