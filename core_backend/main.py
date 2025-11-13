# core_backend/main.py
from fastapi import FastAPI

app = FastAPI(title="Self-Transparent Knowledge Explorer API")

@app.get("/")
def read_root():
    return {"status": "Backend is running"}