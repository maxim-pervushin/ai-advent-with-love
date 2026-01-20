from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
from .base import Provider
from .models import CompletionsResponse


class MistralProvider(Provider):
    """Mistral API provider"""
    
    def __init__(self):
        super().__init__("Mistral")
        self.url = "https://api.mistral.ai/v1/chat/completions"
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Call Mistral API using REST"""
        if not model:
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
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    text = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    
                    return CompletionsResponse(
                        text=text,
                        prompt_tokens=usage.get("prompt_tokens"),
                        completion_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens"),
                        latency=latency
                    )
        except Exception as e:
            print(f"Error calling Mistral API: {e}")
            return None