#!/usr/bin/env python3
"""
RAG search utility using Qdrant DB and Ollama LLM.
Provides RAG-enhanced responses using document context.
"""

import sys
from typing import List, Tuple

import ollama
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


COLLECTION_NAME = "pdf_documents"
EMBEDDING_MODEL = "evilfreelancer/enbeddrus:latest"
RERANKING_MODEL = "nailmarsel/ru-e5-base"
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


def generate_reranking_embedding(text: str) -> List[float]:
    """Generate embedding for text using the reranking model."""
    try:
        response = ollama.embed(model=RERANKING_MODEL, input=text)
        return response["embeddings"][0]
    except Exception as e:
        print(f"Error generating reranking embedding: {e}")
        sys.exit(1)


def rerank_documents(query: str, documents: List[Tuple[str, str, int, float]]) -> List[Tuple[str, str, int, float]]:
    """Rerank documents based on relevance to the query using the reranking model."""
    if not documents:
        return documents
    
    try:
        # Generate query embedding using reranking model
        query_embedding = generate_reranking_embedding(query)
        
        # Generate embeddings for all document contents
        doc_contents = [doc[0] for doc in documents]
        doc_embeddings = []
        
        # Process in batches to avoid memory issues
        batch_size = 10
        for i in range(0, len(doc_contents), batch_size):
            batch = doc_contents[i:i+batch_size]
            batch_embeddings = ollama.embed(model=RERANKING_MODEL, input=batch)
            doc_embeddings.extend(batch_embeddings["embeddings"])
        
        # Calculate cosine similarity between query and each document
        import numpy as np
        from numpy.linalg import norm
        
        query_vec = np.array(query_embedding)
        similarities = []
        
        for doc_embedding in doc_embeddings:
            doc_vec = np.array(doc_embedding)
            # Cosine similarity calculation
            similarity = np.dot(query_vec, doc_vec) / (norm(query_vec) * norm(doc_vec))
            similarities.append(similarity)
        
        # Create new list with updated scores
        reranked_docs = []
        for i, doc in enumerate(documents):
            # Combine original score with reranking score (simple average)
            combined_score = (doc[3] + similarities[i]) / 2
            reranked_docs.append((doc[0], doc[1], doc[2], combined_score))
        
        # Sort by combined score in descending order
        reranked_docs.sort(key=lambda x: x[3], reverse=True)
        
        return reranked_docs
    except Exception as e:
        print(f"Error during reranking: {e}")
        return documents


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
    rag_response: str,
    source_chunks: List[Tuple[str, str, int, float]],
    reranked_response: str = None,
    reranked_chunks: List[Tuple[str, str, int, float]] = None,
):
    """Display RAG response and source chunks."""
    print("\n" + "=" * 60)
    print(f"QUERY: {query}")
    print("=" * 60)

    print("\n" + "-" * 60)
    print("LLM+RAG RESPONSE")
    print("-" * 60)
    print(rag_response)

    # print("\n" + "-" * 60)
    # print(f"SOURCE CHUNKS (Top {len(source_chunks)})")
    # print("-" * 60)

    # for i, (content, source, chunk_idx, score) in enumerate(source_chunks, 1):
    #     print(f"\n[{i}] Source: {source} (chunk {chunk_idx}, similarity: {score:.4f})")
    #     print(f"    Content: {content[:300]}{'...' if len(content) > 300 else ''}")

    if reranked_response and reranked_chunks:
        print("\n" + "-" * 60)
        print("LLM+RAG+RERANKING RESPONSE")
        print("-" * 60)
        print(reranked_response)

        # print("\n" + "-" * 60)
        # print(f"RERANKED SOURCE CHUNKS (Top {len(reranked_chunks)})")
        # print("-" * 60)

        # for i, (content, source, chunk_idx, score) in enumerate(reranked_chunks, 1):
        #     print(f"\n[{i}] Source: {source} (chunk {chunk_idx}, combined score: {score:.4f})")
        #     print(f"    Content: {content[:300]}{'...' if len(content) > 300 else ''}")

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

            # Generate RAG response with original ranking
            context_chunks = [chunk[0] for chunk in search_results]
            print("Generating RAG response...")
            rag_response = generate_rag_response(query_text, context_chunks)

            # Generate RAG+reranking response
            print("Reranking documents...")
            reranked_results = rerank_documents(query_text, search_results)
            reranked_context_chunks = [chunk[0] for chunk in reranked_results]
            print("Generating RAG+reranking response...")
            reranked_response = generate_rag_response(query_text, reranked_context_chunks)

            display_results(query_text, rag_response, search_results, reranked_response, reranked_results)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
