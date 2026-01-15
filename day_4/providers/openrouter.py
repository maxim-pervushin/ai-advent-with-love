from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider
from .config import get_provider_config


class OpenRouterProvider(Provider):
    """OpenRouter API provider"""
    
    def __init__(self, default_model: str = None):
        config = get_provider_config("OpenRouter")
        default_model = default_model or config["default_model"]
        super().__init__("OpenRouter", default_model)
        self.url = config["url"]
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
        self.x_title = os.getenv("OPENROUTER_X_TITLE", "")
    
    async def call_api(self, messages: List[Dict[str, Any]], api_key: str = None, model: str = None, **kwargs) -> Optional[str]:
        """Call OpenRouter API using REST"""
        if not model:
            model = self.default_model
            
        # Use environment variable if no API key provided
        if not api_key:
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
            "messages": messages
        }
        

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    content = result["choices"][0]["message"]["content"]
                    print(content)
                    return content
        except Exception as e:
            print(f"Error calling OpenRouter API: {e}")
            return None