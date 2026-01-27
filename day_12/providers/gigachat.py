import asyncio
import ssl
from typing import Optional, List, Dict, Any
import uuid
import aiohttp
import os
import time
import json
from .base import Provider
from .completion_response import CompletionsResponse


class GigachatProvider(Provider):
    """Gigachat API provider"""
    
    def __init__(self):
        super().__init__("Gigachat")
        self.url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        self.access_token = None

    def _get_connector(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return aiohttp.TCPConnector(ssl=ssl_context)
    
    
    async def _get_token(self):
        # https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/post-token
        api_key = os.getenv("GIGACHAT_API_KEY", "")
        try:
            url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
            
            payload = 'scope=GIGACHAT_API_PERS'
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'RqUID': f'{uuid.uuid4()}',
                'Authorization': f'Basic {api_key}'
            }
            
            # print(headers)

            async with aiohttp.ClientSession(connector=self._get_connector()) as session:
                async with session.post(
                        url=url,
                        data=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.access_token = result["access_token"]
                    else:
                        error_text = await response.text()
                        print(f"Gigachat API error: {response.status} - {error_text}")
                        self.access_token = None

        except asyncio.TimeoutError:
            print("Gigachat API request timed out")
            self.access_token = None
        except Exception as e:
            print(f"Error calling Gigachat API: {str(e)}")
            self.access_token = None


    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Call Gigachat API using REST"""
        if not model:
            model = os.getenv("GIGACHAT_MODEL", "GigaChat")

        if self.access_token is None:
            await self._get_token()

        prompt_text = json.dumps(messages, separators=(',', ':'), ensure_ascii=False)                
        prompt_tokens_calculated = await self.tokenize(prompt_text, model)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "update_interval": 0,
            "temperature": temperature
        }
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession(connector=self._get_connector()) as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    text = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    
                    # Calculate completion tokens using tokenize method
                    completion_tokens_calculated = await self.tokenize(text, model)
                    
                    return CompletionsResponse(
                        text=text,
                        prompt_tokens=usage.get("prompt_tokens"),
                        completion_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens"),
                        prompt_tokens_calculated=prompt_tokens_calculated,
                        completion_tokens_calculated=completion_tokens_calculated,
                        latency=latency
                    )
        except Exception as e:
            print(f"Error calling Gigachat API: {e}")
            return None
    
    async def tokenize(self, text: str, model: str) -> Optional[int]:
        """Get token count for the given text using Gigachat API token count endpoint"""
        if not model:
            model = os.getenv("GIGACHAT_MODEL", "GigaChat")

        if self.access_token is None:
            await self._get_token()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        # Use the dedicated token count endpoint
        token_count_url = "https://gigachat.devices.sberbank.ru/api/v1/tokens/count"
        payload = {
            "model": model,
            "input": [text]
        }
        
        try:
            async with aiohttp.ClientSession(connector=self._get_connector()) as session:
                async with session.post(token_count_url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    # Response is an array with token count info
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("tokens")
                    return None
        except Exception as e:
            print(f"Error getting token count from Gigachat API: {e}")
            return None