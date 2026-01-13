from typing import Dict, Any
from .base import Provider
from .openai import OpenAIProvider
from .ollama import OllamaProvider
from .ollama_cloud import OllamaCloudProvider
from .yandexcloud import YandexCloudProvider
from .gigachat import GigachatProvider
from .openrouter import OpenRouterProvider
from .mistral import MistralProvider


class ProviderFactory:
    """Factory for creating provider instances"""
    
    _providers = {
        # "OpenAI": OpenAIProvider,
        "Ollama": OllamaProvider,
        # "OllamaCloud": OllamaCloudProvider,
        "YandexCloud": YandexCloudProvider,
        "Gigachat": GigachatProvider,
        "OpenRouter": OpenRouterProvider,
        "Mistral": MistralProvider
    }
    
    # Cache for provider instances
    _provider_cache: Dict[str, Provider] = {}
    
    @classmethod
    def create_provider(cls, provider_name: str, **kwargs) -> Provider:
        """Create a provider instance by name"""
        # Create a cache key from provider name and kwargs
        cache_key = f"{provider_name}:{str(sorted(kwargs.items()))}"
        
        # Return cached instance if available
        if cache_key in cls._provider_cache:
            return cls._provider_cache[cache_key]
        
        # Create new instance if not cached
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_instance = provider_class(**kwargs)
        cls._provider_cache[cache_key] = provider_instance
        return provider_instance
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider names"""
        return list(cls._providers.keys())