"""Yandex AI provider for AI Coder"""

import os
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID", "")
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY", "")
YANDEX_MODEL = os.environ.get("YANDEX_MODEL", "yandexgpt-lite/latest")
YANDEX_ENDPOINT = os.environ.get(
    "YANDEX_ENDPOINT", "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
)


class YandexProvider:
    """Provider for interacting with Yandex Cloud AI models"""

    def __init__(self, folder_id: Optional[str] = None, api_key: Optional[str] = None):
        self.folder_id = folder_id or YANDEX_FOLDER_ID
        self.api_key = api_key or YANDEX_API_KEY
        self.model = YANDEX_MODEL
        self.endpoint = YANDEX_ENDPOINT

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Make request to Yandex Cloud"""
        if not self.folder_id or not self.api_key:
            return "Error: YANDEX_FOLDER_ID and YANDEX_API_KEY environment variables must be set."

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})

        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 4000,
            },
            "messages": messages,
        }

        try:
            response = requests.post(
                self.endpoint, json=payload, headers=headers, timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return (
                result.get("result", {})
                .get("alternatives", [{}])[0]
                .get("message", {})
                .get("text", "")
            )
        except requests.exceptions.ConnectionError:
            return f"Error: Cannot connect to Yandex API."
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        """Generate JSON response from Yandex"""
        response = self.generate(prompt, system_prompt)
        return {"raw": response}
