# core_backend/setup_database.py
import sqlite3

DB_NAME = "knowledge_base.db"

# SQL statements to create the initial tables
CREATE_LOCAL_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS local_documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT, -- Comma-separated
    publication_year INTEGER, -- Gregorian
    original_filename TEXT NOT NULL,
    storage_filename TEXT NOT NULL UNIQUE,
    language TEXT(2) NOT NULL, -- 'en' or 'fa'
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_DEFAULT_DOCUMENTS = """
CREATE TABLE IF NOT EXISTS default_documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    publication_year INTEGER,
    storage_filename TEXT NOT NULL UNIQUE,
    language TEXT(2) NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def initialize_database():
    """Creates and initializes the SQLite database and tables."""
    try:
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        print("Database connection established.")

        cur.execute(CREATE_LOCAL_DOCUMENTS)
        print("Table 'local_documents' created or already exists.")

        cur.execute(CREATE_DEFAULT_DOCUMENTS)
        print("Table 'default_documents' created or already exists.")

        con.commit()
        con.close()
        print("Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    initialize_database()