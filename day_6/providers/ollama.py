from typing import Optional, List, Dict, Any
import aiohttp
import os
from .base import Provider


class OllamaProvider(Provider):
    """Ollama API provider"""
    
    def __init__(self):
        super().__init__("Ollama")
        self.url = "http://localhost:11434/v1/chat/completions"
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float) -> Optional[str]:
        """Call Ollama API using REST"""
        model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
            
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        # print(f"OllamaProvider.completions, {temperature}, {model}")

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