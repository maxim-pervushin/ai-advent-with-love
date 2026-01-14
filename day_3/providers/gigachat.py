import asyncio
import ssl
from typing import Optional, List, Dict, Any
import uuid
import aiohttp
import os
from .base import Provider
from .config import get_provider_config


class GigachatProvider(Provider):
    """Gigachat API provider"""
    
    def __init__(self, default_model: str = None):
        config = get_provider_config("Gigachat")
        default_model = default_model or config["default_model"]
        super().__init__("Gigachat", default_model)
        self.url = config["url"]
        self.access_token = None
        print("GigachatProvider.__init__")

    def _get_connector(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return aiohttp.TCPConnector(ssl=ssl_context)
    
    
    async def _get_token(self, api_key: str):
        # https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/post-token
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
                        print(f"Gigachat API: access token received: {self.access_token[:10]}")
                        # print("-" * 50)
                        # print(self.access_token)
                        # print("-" * 50)
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


    async def call_api(self, messages: List[Dict[str, Any]], api_key: str = None, model: str = None, **kwargs) -> Optional[str]:
        """Call Gigachat API using REST"""
        if not model:
            model = self.default_model
            
        # Use environment variable if no API key provided
        if not api_key:
            api_key = os.getenv("GIGACHAT_API_KEY", "")

        if self.access_token is None:
            print(f"Gigachat API: getting access token. Current access token: {self.access_token}")
            await self._get_token(api_key=api_key)
        else:
            print("Gigachat API: using existing access token")

        print(f"Gigachat API: calling API with model: {model}")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "update_interval": 0
        }
        
        # print(headers)
        # print(payload)

        try:
            async with aiohttp.ClientSession(connector=self._get_connector()) as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling Gigachat API: {e}")
            return None