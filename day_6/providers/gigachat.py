import asyncio
import ssl
from typing import Optional, List, Dict, Any
import uuid
import aiohttp
import os
from .base import Provider


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


    async def completions(self, messages: List[Dict[str, Any]], temperature: float) -> Optional[str]:
        """Call Gigachat API using REST"""
        model = os.getenv("GIGACHAT_MODEL", "GigaChat")

        if self.access_token is None:
            # print(f"Gigachat API: getting access token. Current access token: {self.access_token}")
            await self._get_token()
        # else:
        #     print("Gigachat API: using existing access token")

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
        
        try:
            async with aiohttp.ClientSession(connector=self._get_connector()) as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling Gigachat API: {e}")
            return None