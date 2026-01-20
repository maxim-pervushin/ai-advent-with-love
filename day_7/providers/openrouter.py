from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
from .base import Provider
from .models import CompletionsResponse


class OpenRouterProvider(Provider):
    """OpenRouter API provider"""
    
    def __init__(self):
        super().__init__("OpenRouter")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
        self.x_title = os.getenv("OPENROUTER_X_TITLE", "")
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Call OpenRouter API using REST"""
        if not model:
            model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        # Add optional headers if configured
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            headers["X-Title"] = self.x_title
        
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
                    
                    # Print content for debugging (can be removed later)
                    print(text)
                    
                    return CompletionsResponse(
                        text=text,
                        prompt_tokens=usage.get("prompt_tokens"),
                        completion_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens"),
                        latency=latency
                    )
        except Exception as e:
            print(f"Error calling OpenRouter API: {e}")
            return None