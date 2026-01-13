import os
from typing import Dict, Any

SYSTEM_PROMPT_JSON = """
Твоя задача — преобразовать свой ответ в JSON‑массив объектов. Соблюдай строго:
0. Возвращай ТОЛЬКО текст, без какого-либо форматирования markup, html и т.п.
1. Формат вывода — только валидный JSON, без какого‑либо текста до или после и без дополнительного форматирования markup, html и т.п.
2. Каждый элемент массива — объект с двумя полями:
    id: целое число, начиная с 1, по порядку.
    text: строка, содержащая ровно одно предложение.
3. Все предложения из твоего ответа должны быть включены, без пропусков и изменений смысла.
4. Не добавляй никаких других полей, комментариев, пояснений или форматирования вне JSON.
5. Убедись, что JSON валиден и готов к парсингу.

Пример ожидаемого вывода:
[
  {
    "id": 1,
    "text": "Это первое предложение."
  },
  {
    "id": 2,
    "text": "А это второе."
  },
  {
    "id": 3,
    "text": "И так далее."
  }
]"""

SYSTEM_PROMPT_XML = """
Твоя задача — преобразовать свой ответ в XML‑структуру. Соблюдай строго:
0. Возвращай ТОЛЬКО текст, без какого-либо форматирования markup, html и т.п.
1. Формат вывода — только валидный XML, без какого‑либо текста до или после.
2. Корневой элемент должен называться `<sentences>`.
3. Каждый элемент предложения — это тег `<sentence>` с атрибутом `id` (целое число, начиная с 1, по порядку) и текстовым содержимым (ровно одно предложение).
4. Все предложения из твоего ответа должны быть включены, без пропусков и изменений смысла.
5. Не добавляй никаких других атрибутов, комментариев, пояснений или форматирования вне XML.
6. Убедись, что XML валиден и готов к парсингу.

Пример ожидаемого вывода:
<?xml version="1.1" encoding="UTF-8"?>
<sentences>
  <sentence id="1">Это первое предложение.</sentence>
  <sentence id="2">А это второе.</sentence>
  <sentence id="3">И так далее.</sentence>
</sentences>
"""


SYSTEM_PROMPTS = [
    {
        "id": 0,
        "name": "Предложения в JSON",
        "prompt": SYSTEM_PROMPT_JSON
    },
    {
        "id": 1,
        "name": "Предложения в XML",
        "prompt": SYSTEM_PROMPT_XML
    },
]



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
        "folder_id": os.getenv("YANDEXCLOUD_FOLDER_ID"),
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