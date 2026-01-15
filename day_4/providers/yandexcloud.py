import json
from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider
from .config import get_provider_config


class YandexCloudProvider(Provider):
    """YandexCloud API provider"""
    
    def __init__(self, default_model: str = None):
        config = get_provider_config("YandexCloud")
        self.folder_id = config["folder_id"]
        default_model = default_model or config["default_model"]
        super().__init__("YandexCloud", default_model)
        self.url = config["url"]
    
    async def call_api(self, messages: List[Dict[str, Any]], api_key: str = None, model: str = None, **kwargs) -> Optional[str]:
        """Call YandexCloud API using REST"""
        if not model:
            model = self.default_model
            
        # Use environment variable if no API key provided
        if not api_key:
            api_key = os.getenv("YANDEXCLOUD_API_KEY", "")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        yandex_messages = []
        for msg in messages:
            yandex_messages.append({"role": msg["role"], "text": msg["content"]})
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": "1000",
                "reasoningOptions": {
                    "mode": "DISABLED"
                    }
            },
            "messages": yandex_messages
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    text = result["result"]["alternatives"][0]["message"]["text"]
                    return text
        except Exception as e:
            print(f"Error calling YandexCloud API: {e}")
            return None