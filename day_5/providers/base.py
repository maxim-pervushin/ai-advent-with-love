from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class Provider(ABC):
    """Base interface for AI providers"""
    
    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model
    
    @abstractmethod
    async def call_api(self, messages: List[Dict[str, Any]], **kwargs) -> Optional[str]:
        """Call the AI provider API"""
        pass