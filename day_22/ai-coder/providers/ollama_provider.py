"""Ollama AI provider for AI Coder"""

import os
from typing import Optional
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "glm-4.7-flash:latest")


class OllamaProvider:
    """Provider for interacting with Ollama AI models"""

    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.host = OLLAMA_HOST

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Make request to Ollama"""
        url = f"{self.host}/api/generate"
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.ConnectionError:
            return f"Error: Cannot connect to Ollama at {self.host}. Make sure Ollama is running."
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        """Generate JSON response from Ollama"""
        response = self.generate(prompt, system_prompt)

        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response = "\n".join(lines)

            return {"raw": response}
        except Exception:
            return {"raw": response}
