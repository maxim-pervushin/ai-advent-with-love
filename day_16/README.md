# Embedding Search System

This project provides two Python scripts for generating embeddings using Ollama's qwen3-embedding model and performing similarity search using sqlite-vss (FAISS integration).

## Files

- `make_embeddings.py`: Generates embeddings from text documents and stores them in SQLite
- `search.py`: Command-line utility to search for similar documents
- `sample_texts.txt`: Example input file with sample texts

## Requirements

- Python 3.7+
- Ollama with qwen3-embedding:0.6b model
- sqlite-vss Python package

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Ollama from https://ollama.com/

3. Pull the qwen3-embedding model:
   ```bash
   ollama pull qwen3-embedding:0.6b
   ```

## Usage

### 1. Generate Embeddings

```bash
python make_embeddings.py sample_texts.txt
```

This will create an `embeddings.db` file with the documents and their embeddings.

### 2. Search for Similar Documents

```bash
python search.py "artificial intelligence" --limit 3
```

This will search for documents similar to "artificial intelligence" and return the top 3 results.

## How It Works

1. `make_embeddings.py` reads text documents from a file, generates embeddings using Ollama's qwen3-embedding model, and stores both the original texts and embeddings in an SQLite database using sqlite-vss for efficient similarity search.

2. `search.py` takes a query text, generates its embedding, and searches the database for similar documents using FAISS-based vector search.