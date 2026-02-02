#!/usr/bin/env python3
"""
Script to generate embeddings using Ollama's qwen3-embedding model
and store them in SQLite using sqlite-vss (FAISS integration).
"""

import json
import sqlite3
import sys
from typing import List, Tuple

import ollama
import sqlite_vss


def initialize_database(db_path: str = "embeddings.db") -> sqlite3.Connection:
    """Initialize SQLite database with sqlite-vss extension."""
    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vss.load(db)
    
    # Create tables
    db.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            metadata TEXT
        )
    """)
    
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vss_documents USING vss0(
            embedding(768)  -- evilfreelancer/enbeddrus:latest 768 dimensions
        )
    """)
    
    db.commit()
    return db


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts using Ollama."""
    try:
        response = ollama.embed(
            model='evilfreelancer/enbeddrus:latest',
            input=texts
        )
        return response['embeddings']
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        sys.exit(1)


def store_embeddings(db: sqlite3.Connection, texts: List[str], embeddings: List[List[float]], metadata: List[dict] = None):
    """Store texts and their embeddings in the database."""
    if metadata is None:
        metadata = [{}] * len(texts)
    
    cursor = db.cursor()
    
    for i, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadata)):
        # Insert document
        cursor.execute(
            "INSERT INTO documents (content, metadata) VALUES (?, ?)",
            (text, json.dumps(meta))
        )
        doc_id = cursor.lastrowid
        
        # Insert embedding
        cursor.execute(
            "INSERT INTO vss_documents (rowid, embedding) VALUES (?, ?)",
            (doc_id, json.dumps(embedding))
        )
    
    db.commit()
    print(f"Stored {len(texts)} documents and embeddings in the database.")


def load_texts_from_file(file_path: str) -> List[str]:
    """Load texts from a file, one per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)


def main():
    """Main function to generate and store embeddings."""
    if len(sys.argv) < 2:
        print("Usage: python make_embeddings.py <input_file>")
        print("  input_file: Path to a text file with one document per line")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Load texts
    texts = load_texts_from_file(input_file)
    print(f"Loaded {len(texts)} texts from {input_file}")
    
    # Initialize database
    db = initialize_database()
    
    # Generate embeddings in batches
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        # Generate embeddings
        embeddings = generate_embeddings(batch_texts)
        
        # Store in database
        store_embeddings(db, batch_texts, embeddings)
    
    db.close()
    print("Done!")


if __name__ == "__main__":
    main()