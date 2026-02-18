#!/usr/bin/env python3
"""
Ollama AI Service for interacting with Ollama models.
"""

import os
from typing import List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from ai_service.ai_service import AIService


class OllamaAIService(AIService):
    def __init__(self, model_name: str = None):
        """
        Initialize the Ollama AI Service.
        
        Args:
            model_name (str): The Ollama model to use
        """
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME", "glm-4.7-flash:latest")
        self.llm = None
        
    async def initialize(self, tools: Optional[List] = None):
        """Initialize the LLM.
        
        Args:
            tools (List, optional): List of tools (ignored in this implementation)
        """
        print(f"Initializing Ollama model: {self.model_name}")
        
        # Initialize Ollama LLM
        try:
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
            )
            print("✅ Ollama LLM initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Ollama LLM: {e}")
            print("Please ensure Ollama is running and the model is available.")
            raise
            
        print("🚀 Ollama AI Service initialization complete!")
    
    async def chat(self, message: str, chat_history: Optional[List] = None) -> str:
        """
        Send a message to the LLM and get a response.
        
        Args:
            message (str): The user's message
            chat_history (List, optional): Previous conversation history
            
        Returns:
            str: The LLM's response
        """
        if not self.llm:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        if chat_history is None:
            chat_history = []
        
        try:
            # Convert chat history to the format expected by the LLM
            messages = []
            for msg in chat_history:
                if isinstance(msg, HumanMessage):
                    messages.append(("user", msg.content))
                elif isinstance(msg, AIMessage):
                    messages.append(("assistant", msg.content))
            
            messages.append(("user", message))
            
            # Get response from LLM
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error processing request: {str(e)}"
            
    def get_llm(self):
        """Get the initialized LLM instance."""
        return self.llm