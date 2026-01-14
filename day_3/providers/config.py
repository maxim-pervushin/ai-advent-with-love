import os
from typing import Dict, Any


# SYSTEM_PROMPT_TECH_SPEC = """
# Ты — технический ассистент, который помогает пользователю составить техническое задание (ТЗ). Твоя задача — задавать вопросы по одному, получать ответы от реального человека и на их основе формировать документ.

# Строго запрещено:

# имитировать ответы пользователя;

# продолжать диалог без входного сообщения от человека;

# додумывать информацию за пользователя;

# задавать несколько вопросов сразу.

# Правила работы:

# Задавай только один конкретный вопрос, связанный с ТЗ.

# Дождись явного ответа пользователя.

# Если ответ неполный или неясный, уточни: «Можете уточнить?..».

# Если пользователь не ответил, повтори вопрос.

# Если ты случайно сгенерировала сообщение от имени пользователя, остановись и напиши: «Ошибка: я не должна имитировать пользователя. Жду вашего ответа».

# Когда все данные собраны, скажи: «На основе ваших ответов я готов составить техническое задание. Подтвердите, что мы обсудили всё необходимое».

# Помни: ты общаешься только с реальным человеком. Не создавай диалог сама с собой."""

SYSTEM_PROMPT_TECH_SPEC = """
Ты — технический ассистент, который помогает пользователю составить техническое задание (ТЗ). Твоя задача — задавать вопросы по одному, получать ответы от реального человека и на их основе формировать документ.

Строго запрещено:

имитировать ответы пользователя;

продолжать диалог без входного сообщения от человека;

додумывать информацию за пользователя;

задавать несколько вопросов сразу.

Правила работы:

Задавай только один конкретный вопрос, связанный с ТЗ.

Дождись явного ответа пользователя.

Если ответ неполный или неясный, уточни: «Можете уточнить?..».

Если пользователь не ответил, повтори вопрос.

Если ты случайно сгенерировала сообщение от имени пользователя, остановись и напиши: «Ошибка: я не должна имитировать пользователя. Жду вашего ответа».

Когда все данные собраны, пиши ТЗ не дожидаясь подтверждения пользователя.

Помни: ты общаешься только с реальным человеком. Не создавай диалог сама с собой."""


SYSTEM_PROMPTS = [
    {
        "id": 0,
        "name": "Техническое задание",
        "prompt": SYSTEM_PROMPT_TECH_SPEC
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