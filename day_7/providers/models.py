from dataclasses import dataclass
from typing import Optional


@dataclass
class CompletionsResponse:
    """Response from AI provider completions API"""
    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency: Optional[float] = None