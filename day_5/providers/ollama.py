from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider
from .config import get_provider_config


class OllamaProvider(Provider):
    """Ollama API provider"""
    
    def __init__(self, default_model: str = None):
        config = get_provider_config("Ollama")
        default_model = default_model or config["default_model"]
        super().__init__("Ollama", default_model)
        self.url = config["url"]
    
    async def call_api(self, messages: List[Dict[str, Any]], model: str = None, **kwargs) -> Optional[str]:
        """Call Ollama API using REST"""
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
            print("Error: Could not connect to Ollama. Please ensure Ollama is running on localhost:11434")
            return None
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                print(f"Error: Model '{model}' not found in Ollama. Please pull the model first with 'ollama pull {model}'")
            else:
                print(f"Error calling Ollama API: {e}")
            return None
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
            return None