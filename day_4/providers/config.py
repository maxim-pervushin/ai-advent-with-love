import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True, verbose=True)

# Provider configurations
PROVIDER_CONFIGS = {
    "OpenAI": {
        "url": "https://api.openai.com/v1/chat/completions",
        "default_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        # "system_prompt": SYSTEM_PROMPT
    },
    "Ollama": {
        "url": "http://localhost:11434/v1/chat/completions",
        "default_model": os.getenv("OLLAMA_MODEL", "llama3.2"),
        # "system_prompt": SYSTEM_PROMPT
    },
    "OllamaCloud": {
        "url": "https://ollama.com/api/v1/chat/completions",
        "default_model": os.getenv("OLLAMA_CLOUD_MODEL", "llama3.2"),
        # "system_prompst": SYSTEM_PROMPT
    },
    "YandexCloud": {
        "url": "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        "default_model": os.getenv("YANDEXCLOUD_MODEL", "yandexgpt-lite/latest"),
        "folder_id": os.getenv("YANDEXCLOUD_FOLDER_ID", ""),
        # "system_prompt": SYSTEM_PROMPT
    },
    "Gigachat": {
        "url": "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        "default_model": os.getenv("GIGACHAT_MODEL", "GigaChat"),
        # "system_prompt": SYSTEM_PROMPT
    },
    "OpenRouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free"),
        # "system_prompt": SYSTEM_PROMPT
    },
    "Mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "default_model": os.getenv("MISTRAL_MODEL", "mistral-tiny"),
        # "system_prompt": SYSTEM_PROMPT
    }
}


def get_provider_config(provider_name: str) -> Dict[str, Any]:
    """Get configuration for a specific provider"""
    return PROVIDER_CONFIGS.get(provider_name, PROVIDER_CONFIGS["OpenAI"])