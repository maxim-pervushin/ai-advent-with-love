import json
from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
from tokenizers import Tokenizer, normalizers
from .base import Provider
from .completion_response import CompletionsResponse


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

        # Extract prompt text for token calculation
        # prompt_text = ""
        # for message in messages:
        #     if message.get("content"):
        #         prompt_text += message["content"] + " "

        prompt_text = json.dumps(messages, separators=(',', ':'), ensure_ascii=False)
        prompt_tokens_calculated = await self.tokenize(prompt_text, model)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    text = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    
                    # Calculate tokens using tokenize method
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
    
    async def tokenize(self, text: str, model: str) -> Optional[int]:
        """Get token count for the given text using Hugging Face tokenizers"""
        try:
            # Use Hugging Face tokenizers with authorization
            # Use GPT-2 tokenizer as a general-purpose tokenizer
            # It works well for most models including Llama, Mistral, etc.
            hf_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
            tokenizer = Tokenizer.from_pretrained("Qwen/Qwen3-0.6B", token=hf_token)
            # tokenizer.normalizer = normalizers.Sequence([
            #     normalizers.NFD(),      # Разложение Unicode (é → e + `)
            #     normalizers.StripAccents(),  # Удаление диакритики
            #     normalizers.Replace(" ", "▁")  # Spaces как в BPE
            # ])
            # Tokenize the text
            encoding = tokenizer.encode(text)
            return len(encoding.ids)
        except Exception as e:
            print(f"Error tokenizing text with Hugging Face tokenizers: {e}")
            return None
    