#!/usr/bin/env python3
"""
RAG search utility using Qdrant DB and Ollama LLM.
Provides RAG-enhanced response.
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

def generate_rag_response(query: str, context_chunks: List[str]) -> Tuple[str, str]:
    """Generate RAG-enhanced response using context chunks and return both response and source quote."""
    context = "\n\n".join(context_chunks)
    
    # Use only the first chunk as the source quote
    source_quote = context_chunks[0] if context_chunks else ""
    
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful assistant. Use the following context to answer the user's question. Always include a direct quote from the context that supports your answer. Format your response as: [QUOTE]\"...\"[/QUOTE] Your answer here.\nContext:\n{context}\nIf the context doesn't contain relevant information to answer the question, say so.",
                },
                {"role": "user", "content": query},
            ],
        )
        return response["message"]["content"], source_quote
    except Exception as e:
        return f"Error generating response: {e}", source_quote


def display_results(
    query: str,
    rag_response: str,
    # source_quote: str,
    # source_chunks: List[Tuple[str, str, int, float]],
):
    """Display RAG response and source chunks."""
    # print("\n" + "=" * 60)
    # print(f"QUERY: {query}")
    # print("=" * 60)
    
    # print("\n" + "-" * 60)
    # print("LLM+RAG RESPONSE")
    # print("-" * 60)
    print(f"AI: {rag_response}")


def main():
    """Main REPL loop for RAG search."""
    print("RAG Search with Qdrant and Ollama")
    print("Using model: " + LLM_MODEL)
    print("Enter 'quit' or 'exit' to stop the program.")
    print("-" * 40)

    client = initialize_qdrant()

    try:
        while True:
            query_text = input("\User: ").strip()

            if query_text.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not query_text:
                print("Please enter a valid question.")
                continue

            # print("Searching for relevant documents...")
            search_results = search_similar_documents(client, query_text, 5)

            if not search_results:
                print("\nNo relevant documents found in the database.")
                print("Make sure to run make_embeddings.py first to populate Qdrant.")
                continue

            context_chunks = [chunk[0] for chunk in search_results]

            # print("Generating response...")

            rag_response, source_quote = generate_rag_response(query_text, context_chunks)
            
            display_results(query_text, rag_response)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
