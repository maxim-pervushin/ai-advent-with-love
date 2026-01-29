from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
from tokenizers import Tokenizer
from .base import Provider
from .completion_response import CompletionsResponse


class MistralProvider(Provider):
    """Mistral API provider"""
    
    def __init__(self):
        super().__init__("Mistral")
        self.url = "https://api.mistral.ai/v1/chat/completions"
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Call Mistral API using REST"""
        if not model:
            model = os.getenv("MISTRAL_MODEL", "mistral-tiny")
        api_key = os.getenv("MISTRAL_API_KEY", "")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        # Extract prompt text for token calculation
        prompt_text = ""
        for message in messages:
            if message.get("content"):
                prompt_text += message["content"] + " "
                
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()
                    latency = time.time() - start_time
                    
                    text = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    
                    # Calculate tokens using tokenize method
                    prompt_tokens_calculated = await self.tokenize(prompt_text, model)
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
            print(f"Error calling Mistral API: {e}")
            return None
    
    async def tokenize(self, text: str, model: str) -> Optional[int]:
        """Get token count for the given text using Hugging Face tokenizers"""
        try:
            # Use Hugging Face tokenizers with authorization
            # Use GPT-2 tokenizer as a general-purpose tokenizer
            # It works well for most models including Llama, Mistral, etc.
            hf_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
            tokenizer = Tokenizer.from_pretrained("gpt2", token=hf_token)
            
            # Tokenize the text
            encoding = tokenizer.encode(text)
            return len(encoding.ids)
        except Exception as e:
            print(f"Error tokenizing text with Hugging Face tokenizers: {e}")
            return None
    