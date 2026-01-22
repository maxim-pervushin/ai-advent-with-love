import asyncio
import json

from dotenv import load_dotenv
import os

import tiktoken
from providers import GigachatProvider, OllamaProvider, OpenRouterProvider, YandexCloudProvider, MistralProvider
from providers.base import Provider
from providers.completion_response import CompletionsResponse

async def print_completion(provider_instance: Provider, model: str, prompt: str):
    """Print completion and tokens info for the user request."""
    print(f"Provider: {provider_instance.name}")
    print(f"Model: {model}")
    print(f"Prompt: {prompt}")
    
    response = await provider_instance.completions(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        model=model
    )
    
    if response:
        print(f"AI:\n{response.text}")
        print('Tokens.')
        print(f"Provided. prompt={response.prompt_tokens}, completion={response.completion_tokens}")
        print(f"Calculated. prompt={response.prompt_tokens_calculated}, completion={response.completion_tokens_calculated}")
    else:
        print("AI: No response received")

if __name__ == "__main__":
    
    load_dotenv(override=True)

    # https://ollama.com/library/qwen3:4b
    # asyncio.run(print_completion(OllamaProvider(), "qwen3:0.6b", "быстрая сортировка на python"))
    asyncio.run(print_completion(GigachatProvider(), "GigaChat-2", "быстрая сортировка на python"))
