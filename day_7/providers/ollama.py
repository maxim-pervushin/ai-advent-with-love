from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
from .base import Provider
from .models import CompletionsResponse


class OllamaProvider(Provider):
    """Ollama API provider"""
    
    def __init__(self):
        super().__init__("Ollama")
        self.url = "http://localhost:11434/v1/chat/completions"
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Call Ollama API using REST"""
        if not model:
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
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    text = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    
                    return CompletionsResponse(
                        text=text,
                        prompt_tokens=usage.get("prompt_tokens"),
                        completion_tokens=usage.get("completion_tokens"),
                        total_tokens=usage.get("total_tokens"),
                        latency=latency
                    )
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