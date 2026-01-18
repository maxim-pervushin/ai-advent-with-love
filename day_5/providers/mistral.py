from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider
from .config import get_provider_config


class MistralProvider(Provider):
    """Mistral API provider"""
    
    def __init__(self, default_model: str = None):
        config = get_provider_config("Mistral")
        default_model = default_model or config["default_model"]
        super().__init__("Mistral", default_model)
        self.url = config["url"]
    
    async def call_api(self, messages: List[Dict[str, Any]], api_key: str = None, model: str = None, **kwargs) -> Optional[str]:
        """Call Mistral API using REST"""
        if not model:
            model = self.default_model
            
        # Use environment variable if no API key provided
        if not api_key:
            api_key = os.getenv("MISTRAL_API_KEY", "")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
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
            print(f"Error calling Mistral API: {e}")
            return None