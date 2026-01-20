import json
from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
from .base import Provider
from .models import CompletionsResponse


class YandexCloudProvider(Provider):
    """YandexCloud API provider"""
    
    def __init__(self):
        super().__init__("YandexCloud")
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.folder_id = os.getenv("YANDEXCLOUD_FOLDER_ID", "")
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Call YandexCloud API using REST"""
        if not model:
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
                # "reasoningOptions": {
                #     "mode": "DISABLED"
                #     }
            },
            "messages": yandex_messages
        }

        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    text = result["result"]["alternatives"][0]["message"]["text"]
                    usage = result["result"].get("usage", {})
                    
                    return CompletionsResponse(
                        text=text,
                        prompt_tokens=usage.get("inputTextTokens"),
                        completion_tokens=usage.get("completionTokens"),
                        total_tokens=usage.get("totalTokens"),
                        latency=latency
                    )
        except Exception as e:
            print(f"Error calling YandexCloud API: {e}")
            return None