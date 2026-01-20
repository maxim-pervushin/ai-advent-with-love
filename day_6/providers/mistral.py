from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider


class MistralProvider(Provider):
    """Mistral API provider"""
    
    def __init__(self):
        super().__init__("Mistral")
        self.url = "https://api.mistral.ai/v1/chat/completions"
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float) -> Optional[str]:
        """Call Mistral API using REST"""
        model = os.getenv("MISTRAL_MODEL", "mistral-tiny")
        api_key = os.getenv("MISTRAL_API_KEY", "")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
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