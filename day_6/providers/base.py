from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class Provider(ABC):
    """Base interface for AI providers"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def completions(self, messages: List[Dict[str, Any]], temperature: float) -> Optional[str]:
        """Get completions from the AI provider"""
        pass