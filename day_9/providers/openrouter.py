from typing import Optional, List, Dict, Any
import aiohttp
import os
import time
from tokenizers import Tokenizer
from .base import Provider
from .completion_response import CompletionsResponse


class OpenRouterProvider(Provider):
    """OpenRouter API provider"""
    
    def __init__(self):
        super().__init__("OpenRouter")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.http_referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
        self.x_title = os.getenv("OPENROUTER_X_TITLE", "")
    
    async def completions(self, messages: List[Dict[str, Any]], temperature: float, model: str) -> Optional[CompletionsResponse]:
        """Call OpenRouter API using REST"""
        if not model:
            model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        # Add optional headers if configured
        if self.http_referer:
            headers["HTTP-Referer"] = self.http_referer
        if self.x_title:
            headers["X-Title"] = self.x_title
        
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
        
        prompt_tokens_calculated = await self.tokenize(prompt_text, model)

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
            print(f"Error calling OpenRouter API: {e}")
            return None
    
    async def tokenize(self, text: str, model: str) -> Optional[int]:
        """Get token count for the given text using Hugging Face tokenizers"""
        try:
            # Use Hugging Face tokenizers with authorization
            # Use GPT-2 tokenizer as a general-purpose tokenizer
            # It works well for most models including Llama, Mistral, etc.
            hf_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
            tokenizer = Tokenizer.from_pretrained("qwen/qwen3-4b", token=hf_token)
            
            # Tokenize the text
            encoding = tokenizer.encode(text)
            return len(encoding.ids)
        except Exception as e:
            print(f"Error tokenizing text with Hugging Face tokenizers: {e}")
            return None
    