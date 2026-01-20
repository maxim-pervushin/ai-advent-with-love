import asyncio

from dotenv import load_dotenv
import os
from providers.gigachat import GigachatProvider
from providers.ollama import OllamaProvider
from providers.openrouter import OpenRouterProvider
from providers.yandexcloud import YandexCloudProvider

async def main(prompts: list[str], temperatures: list[float], repeats: int):
    for prompt in prompts:
        print(f"USER: {prompt}")
        for temperature in temperatures:
            for idx in range(repeats):
                # provider_instance = YandexCloudProvider()
                provider_instance = OllamaProvider() # llama3.2:1b
                # provider_instance = OpenRouterProvider()
                # provider_instance = GigachatProvider()
                messages = []
                messages.append({"role": "user", "content": prompt})
                response = await provider_instance.completions(messages=messages, temperature=temperature)
                print(f"\nAI [{idx}, t:{temperature}]:\n{response}")

if __name__ == "__main__":
    
    load_dotenv(override=True)

    prompts = [
        # "Составь стих о море.",
        "Придумай 3 идеи подарков. Только идеи, без детализации.",
        # "Расскажи анекдот.",
        # "2 + 2 * 2",
    ]
    
    temperatures = [0, 0.5, 1, ]

    repeats = 3

    asyncio.run(main(prompts, temperatures, repeats))