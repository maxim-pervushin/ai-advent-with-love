from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider
from .config import get_provider_config


class OpenAIProvider(Provider):
    """OpenAI API provider"""
    
    def __init__(self, default_model: str = None):
        config = get_provider_config("OpenAI")
        default_model = default_model or config["default_model"]
        super().__init__("OpenAI", default_model)
        self.url = config["url"]
    
    async def call_api(self, messages: List[Dict[str, Any]], api_key: str = None, model: str = None, **kwargs) -> Optional[str]:
        """Call OpenAI API using REST"""
        if not model:
            model = self.default_model
            
        # Use environment variable if no API key provided
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY", "")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None