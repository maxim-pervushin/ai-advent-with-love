import json
from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider


class YandexCloudProvider(Provider):
    """YandexCloud API provider"""
    
    def __init__(self):
        super().__init__("YandexCloud")
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.folder_id = os.getenv("YANDEXCLOUD_FOLDER_ID", "")
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float) -> Optional[str]:
        """Call YandexCloud API using REST"""
        model = os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest")
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
                "temperature": temperature,
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