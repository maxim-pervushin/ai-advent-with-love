#!/usr/bin/env python3
"""
REPL utility to search for similar texts using embeddings stored in SQLite.
"""

import json
import sqlite3
import sys

import ollama
import sqlite_vss


def initialize_database(db_path: str = "embeddings.db") -> sqlite3.Connection:
    """Initialize SQLite database with sqlite-vss extension."""
    try:
        db = sqlite3.connect(db_path)
        db.enable_load_extension(True)
        sqlite_vss.load(db)
        return db
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


def generate_query_embedding(text: str) -> list:
    """Generate embedding for the query text using Ollama."""
    try:
        response = ollama.embed(
            model='evilfreelancer/enbeddrus:latest',
            input=text
        )
        return response['embeddings'][0]
    except Exception as e:
        print(f"Error generating query embedding: {e}")
        sys.exit(1)


def search_similar_documents(db: sqlite3.Connection, query_embedding: list, limit: int = 5) -> list:
    """Search for similar documents in the database."""
    try:
        query_vector = json.dumps(query_embedding)
        
        results = db.execute("""
            SELECT d.id, d.content, d.metadata, v.distance
            FROM vss_documents v
            JOIN documents d ON d.id = v.rowid
            WHERE vss_search(embedding, vss_search_params(?, ?))
            ORDER BY v.distance
        """, (query_vector, limit)).fetchall()
        
        return results
    except Exception as e:
        print(f"Error searching documents: {e}")
        sys.exit(1)


def display_results(results):
    """Display search results in a formatted way."""
    if results:
        print(f"\nFound {len(results)} similar documents:\n")
        for i, (doc_id, content, metadata, distance) in enumerate(results, 1):
            print(f"{i}. Document ID: {doc_id}")
            print(f"   Distance: {distance:.4f}")
            print(f"   Content: {content[:200]}{'...' if len(content) > 200 else ''}")
            if metadata and metadata != '{}':
                print(f"   Metadata: {metadata}")
            print()
    else:
        print("No similar documents found.")


def main():
    """Main REPL loop for searching similar documents."""
    print("Similarity Search REPL")
    print("Enter 'quit' or 'exit' to stop the program.")
    print("-" * 40)
    
    # Initialize database
    db = initialize_database()
    
    try:
        while True:
            # Get user input
            query_text = input("\nEnter search term: ").strip()
            
            # Check for exit commands
            if query_text.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            # Skip empty queries
            if not query_text:
                print("Please enter a valid search term.")
                continue
            
            # Generate query embedding
            print("Generating embedding for query...")
            query_embedding = generate_query_embedding(query_text)
            
            # Search for similar documents
            print("Searching for similar documents...")
            results = search_similar_documents(db, query_embedding, 5)
            
            # Display results
            display_results(results)
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()