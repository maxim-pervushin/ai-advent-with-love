#!/usr/bin/env python3
"""
RAG search utility using Qdrant DB and Ollama LLM.
Provides both plain LLM response and RAG-enhanced response.
"""

import sys
from typing import List, Tuple

import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SearchRequest


COLLECTION_NAME = "pdf_documents"
EMBEDDING_MODEL = "evilfreelancer/enbeddrus:latest"
LLM_MODEL = "qwen3:8b"
# LLM_MODEL = "llama3.2:1b"


def initialize_qdrant(url: str = "http://localhost:6333") -> QdrantClient:
    """Initialize Qdrant client."""
    return QdrantClient(url=url)


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using Ollama."""
    try:
        response = ollama.embed(model=EMBEDDING_MODEL, input=text)
        return response["embeddings"][0]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        sys.exit(1)


def search_similar_documents(
    client: QdrantClient, query: str, limit: int = 5
) -> List[Tuple[str, str, int, float]]:
    """Search for similar documents in Qdrant."""
    try:
        query_embedding = generate_embedding(query)

        results = client.query_points(
            collection_name=COLLECTION_NAME, query=query_embedding, limit=limit
        )

        documents = []
        for hit in results.points:
            payload = hit.payload
            documents.append(
                (
                    payload.get("content", ""),
                    payload.get("source", "unknown"),
                    payload.get("chunk_index", 0),
                    hit.score,
                )
            )

        return documents
    except Exception as e:
        print(f"Error searching documents: {e}")
        return []


def generate_plain_response(query: str) -> str:
    """Generate plain LLM response without RAG context."""
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer the user's question directly.",
                },
                {"role": "user", "content": query},
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error generating response: {e}"


def generate_rag_response(query: str, context_chunks: List[str]) -> str:
    """Generate RAG-enhanced response using context chunks."""
    context = "\n\n".join(context_chunks)

    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful assistant. Use the following context to answer the user's question.\nContext:\n{context}\nIf the context doesn't contain relevant information to answer the question, say so.",
                },
                {"role": "user", "content": query},
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error generating response: {e}"


def display_results(
    query: str,
    plain_response: str,
    rag_response: str,
    source_chunks: List[Tuple[str, str, int, float]],
):
    """Display both responses and source chunks."""
    print("\n" + "=" * 60)
    print(f"QUERY: {query}")
    print("=" * 60)

    print("\n" + "-" * 60)
    print("1. PLAIN LLM RESPONSE (No RAG)")
    print("-" * 60)
    print(plain_response)

    print("\n" + "-" * 60)
    print("2. LLM+RAG RESPONSE")
    print("-" * 60)
    print(rag_response)

    print("\n" + "-" * 60)
    print(f"SOURCE CHUNKS (Top {len(source_chunks)})")
    print("-" * 60)

    for i, (content, source, chunk_idx, score) in enumerate(source_chunks[:1], 1):
        print(f"\n[{i}] Source: {source} (chunk {chunk_idx}, similarity: {score:.4f})")
        print(f"    Content: {content[:300]}{'...' if len(content) > 300 else ''}")

    print("\n" + "=" * 60)


def main():
    """Main REPL loop for RAG search."""
    print("RAG Search with Qdrant and Ollama")
    print("Using model: " + LLM_MODEL)
    print("Enter 'quit' or 'exit' to stop the program.")
    print("-" * 40)

    client = initialize_qdrant()

    try:
        while True:
            query_text = input("\nEnter your question: ").strip()

            if query_text.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not query_text:
                print("Please enter a valid question.")
                continue

            print("Searching for relevant documents...")
            search_results = search_similar_documents(client, query_text, 5)

            if not search_results:
                print("\nNo relevant documents found in the database.")
                print("Make sure to run make_embeddings.py first to populate Qdrant.")
                continue

            context_chunks = [chunk[0] for chunk in search_results]

            print("Generating responses...")

            plain_response = generate_plain_response(query_text)
            rag_response = generate_rag_response(query_text, context_chunks)

            display_results(query_text, plain_response, rag_response, search_results)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
