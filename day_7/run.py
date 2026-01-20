import asyncio

from dotenv import load_dotenv
import os
from providers import GigachatProvider, OllamaProvider, OpenRouterProvider, YandexCloudProvider, MistralProvider
from providers.models import CompletionsResponse

async def main(prompts: list[str], provider_configs: list):
    for prompt in prompts:
        print(f"\nUSER:\n{prompt}")
        print()

        for provider_class, model_name in provider_configs:
            provider_instance = provider_class()
            print(f"Provider: {provider_instance.name}")
            print(f"Model: {model_name}")
        
            # await asyncio.sleep(5)
            response = await provider_instance.completions(messages=[{"role": "user", "content": prompt}], 
                                                           temperature=0.2, 
                                                           model=model_name)
            if response:
                if response.prompt_tokens is not None:
                    print(f"Tokens: prompt={response.prompt_tokens}, completion={response.completion_tokens}, total={response.total_tokens}, latency={response.latency:.2f}s")
                print(f"AI:\n{response.text}")
            else:
                print("AI: No response received")
                
            print(f"{'='*50}")

if __name__ == "__main__":
    
    load_dotenv(override=True)

    prompts = [
        # "Составь стих о море.",
        # "Придумай 3 идеи подарков. Только идеи, без детализации.",
        # "Расскажи анекдот.",
        # "2 + 2 * 2",
        "быстрая сортировка на python"
    ]
    
    # Define the providers to test with their models
    provider_configs = [
        (YandexCloudProvider, "aliceai-llm"),
        (YandexCloudProvider, "yandexgpt-lite"),
        # (YandexCloudProvider, "qwen3-235b-a22b-fp8/latest"),
        # (YandexCloudProvider, "gpt-oss-120b/latest"),
        # (YandexCloudProvider, "gpt-oss-20b/latest"),
        # (YandexCloudProvider, "gemma-3-27b-it/latest"),
        (OllamaProvider, "llama3.2:1b"),
        # (OpenRouterProvider, "meta-llama/llama-3.2-3b-instruct:free"),
        # (GigachatProvider, "GigaChat"),
        (MistralProvider, "mistral-tiny"),
    ]
    
    asyncio.run(main(prompts, provider_configs))