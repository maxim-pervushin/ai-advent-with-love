from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider
from .config import get_provider_config


class OllamaCloudProvider(Provider):
    """Ollama Cloud API provider"""
    
    def __init__(self, default_model: str = None):
        config = get_provider_config("OllamaCloud")
        default_model = default_model or config["default_model"]
        super().__init__("OllamaCloud", default_model)
        self.url = config["url"]
    
    async def call_api(self, messages: List[Dict[str, Any]], model: str = None, **kwargs) -> Optional[str]:
        """Call Ollama Cloud API using REST"""
        if not model:
            model = self.default_model
            
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except aiohttp.ClientConnectorError:
            print("Error: Could not connect to Ollama Cloud. Please check your network connection and API endpoint")
            return None
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                print(f"Error: Model '{model}' not found in Ollama Cloud.")
            else:
                print(f"Error calling Ollama Cloud API: {e}")
            return None
        except Exception as e:
            print(f"Error calling Ollama Cloud API: {e}")
            return None