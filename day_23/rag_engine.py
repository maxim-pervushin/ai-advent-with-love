"""RAG Engine for Educational Platform Support Assistant"""

import os
from typing import List, Dict
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document


class RAGEngine:
    """RAG Engine to process documentation and provide context for support assistant"""
    
    def __init__(self, docs_path: str = "docs"):
        """Initialize the RAG engine with documentation path"""
        self.docs_path = docs_path
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_store = None
        self._load_documents()
    
    def _load_documents(self) -> None:
        """Load and process all markdown documents in the docs directory"""
        documents = []
        
        # Define headers to split on
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        # Process each markdown file in the docs directory
        for filename in os.listdir(self.docs_path):
            if filename.endswith(".md"):
                file_path = os.path.join(self.docs_path, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                # Split document by headers
                text_splitter = MarkdownHeaderTextSplitter(
                    headers_to_split_on=headers_to_split_on
                )
                splits = text_splitter.split_text(content)
                
                # Add metadata to each split
                for i, split in enumerate(splits):
                    split.metadata["source"] = filename
                    split.metadata["split_index"] = i
                
                documents.extend(splits)
        
        # Create vector store
        if documents:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
    
    def search_context(self, query: str, k: int = 4) -> List[Document]:
        """Search for relevant context based on the query"""
        if not self.vector_store:
            return []
        
        return self.vector_store.similarity_search(query, k=k)
    
    def get_context_string(self, query: str, k: int = 4) -> str:
        """Get relevant context as a string for LLM processing"""
        documents = self.search_context(query, k)
        context_parts = []
        
        for doc in documents:
            content = doc.page_content
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"Из документа {source}:\n{content}")
        
        return "\n\n".join(context_parts)


# Example usage
if __name__ == "__main__":
    rag = RAGEngine()
    context = rag.get_context_string("Как восстановить пароль?")
    print(context)