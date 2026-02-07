#!/usr/bin/env python3
"""
Script to generate embeddings from PDF documents and store them in Qdrant DB.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from pypdf import PdfReader


COLLECTION_NAME = "pdf_documents"
EMBEDDING_MODEL = "evilfreelancer/enbeddrus:latest"
VECTOR_SIZE = 768


def get_pdf_files(pdfs_dir: str) -> List[Path]:
    """Get all PDF files from the specified directory."""
    pdf_path = Path(pdfs_dir)
    if not pdf_path.exists():
        print(f"Directory {pdfs_dir} not found.")
        sys.exit(1)

    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdfs_dir}.")
        sys.exit(1)

    return pdf_files


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a single PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk)

        if end >= text_len:
            break

        start = end - overlap

    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts using Ollama."""
    try:
        response = ollama.embed(model=EMBEDDING_MODEL, input=texts)
        return response["embeddings"]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        sys.exit(1)


def initialize_qdrant(url: str = "http://localhost:6333") -> QdrantClient:
    """Initialize Qdrant client and create collection if needed."""
    client = QdrantClient(url=url)

    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"Created collection '{COLLECTION_NAME}'")
    else:
        print(f"Using existing collection '{COLLECTION_NAME}'")

    return client


def store_embeddings(
    client: QdrantClient,
    chunks: List[str],
    embeddings: List[List[float]],
    pdf_name: str,
    start_index: int,
):
    """Store text chunks and their embeddings in Qdrant."""
    points = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        global_index = start_index + i
        point_id = hash(f"{pdf_name}_{global_index}") % (2**63 - 1)

        payload = {"content": chunk, "source": pdf_name, "chunk_index": global_index}

        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

    client.upsert(collection_name=COLLECTION_NAME, points=points)

    print(
        f"Stored {len(chunks)} chunks from {pdf_name} (indices {start_index}-{start_index + len(chunks) - 1})"
    )


def process_pdfs(pdfs_dir: str, client: QdrantClient, batch_size: int = 10):
    """Process all PDF files and store their embeddings."""
    pdf_files = get_pdf_files(pdfs_dir)
    total_chunks = 0
    global_chunk_index = 0

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")

        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"  No text extracted from {pdf_path.name}")
            continue

        chunks = chunk_text(text)
        print(f"  Extracted {len(chunks)} chunks")

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            print(
                f"  Processing batch {i // batch_size + 1}/{(len(chunks) - 1) // batch_size + 1}"
            )

            embeddings = generate_embeddings(batch_chunks)
            store_embeddings(
                client, batch_chunks, embeddings, pdf_path.name, global_chunk_index
            )
            global_chunk_index += len(batch_chunks)
            total_chunks += len(batch_chunks)

    print(f"\nDone! Total chunks stored: {total_chunks}")


def main():
    """Main function to process PDFs and generate embeddings."""
    pdfs_dir = "pdfs"

    if not os.path.exists(pdfs_dir):
        print(f"PDFs directory '{pdfs_dir}' not found. Creating it...")
        os.makedirs(pdfs_dir)
        print(f"Please add PDF files to the '{pdfs_dir}' directory and run again.")
        sys.exit(0)

    print("Initializing Qdrant connection...")
    client = initialize_qdrant()

    print(f"\nProcessing PDFs from '{pdfs_dir}' directory...")
    process_pdfs(pdfs_dir, client)


if __name__ == "__main__":
    main()
