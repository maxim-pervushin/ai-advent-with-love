from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .completion_response import CompletionsResponse


class Provider(ABC):
    """Base interface for AI providers"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str, tools: Optional[List[Dict[str, Any]]] = None) -> Optional[CompletionsResponse]:
        """Get completions from the AI provider"""
        pass
    
    @abstractmethod
    async def tokenize(self, text: str, model: str) -> Optional[int]:
        """Get token count for the given text"""
        pass

