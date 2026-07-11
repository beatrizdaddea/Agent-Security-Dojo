from typing import Any

import requests

from app.config import settings


class OpenRouterClient:
    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model)

    def chat(self, messages: list[dict[str, str]]) -> str:
        if not self.enabled:
            raise RuntimeError("OpenRouter nao configurado. Use .env para habilitar.")
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages},
            timeout=30,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data["choices"][0]["message"]["content"]

