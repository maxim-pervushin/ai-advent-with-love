#!/usr/bin/env python3
"""
AI Service interface for interacting with different AI models.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AIService(ABC):
    """Abstract base class for AI services."""
    
    @abstractmethod
    async def initialize(self, tools: Optional[List] = None):
        """
        Initialize the AI service.
        
        Args:
            tools (List, optional): List of tools to bind to the service
        """
        pass
    
    @abstractmethod
    async def chat(self, message: str, chat_history: Optional[List] = None) -> str:
        """
        Send a message to the AI service and get a response.
        
        Args:
            message (str): The user's message
            chat_history (List, optional): Previous conversation history
            
        Returns:
            str: The AI service's response
        """
        pass
    
    @abstractmethod
    def get_llm(self):
        """
        Get the underlying LLM instance.
        
        Returns:
            The LLM instance
        """
        pass