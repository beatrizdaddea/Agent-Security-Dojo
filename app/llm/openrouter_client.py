from time import perf_counter
from typing import Any

import requests

from app.config import Settings
from app.schemas.messages import AssistantTurn, CompletionResponse, ModelTelemetry

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(self, model: str | None = None) -> None:
        self.settings = Settings.from_env(model)
        self.model = self.settings.openrouter_model

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> tuple[AssistantTurn, ModelTelemetry]:
        start = perf_counter()
        try:
            response = requests.post(
                OPENROUTER_ENDPOINT,
                headers={"Authorization": f"Bearer {self.settings.openrouter_api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "provider": {"require_parameters": True},
                    "temperature": 0,
                    "max_completion_tokens": 1024,
                },
                timeout=self.settings.openrouter_timeout_seconds,
                allow_redirects=False,
            )
        except requests.Timeout:
            raise OpenRouterError("OpenRouter request timed out.") from None
        except requests.RequestException:
            raise OpenRouterError("Could not connect to OpenRouter.") from None

        if response.status_code != 200:
            raise OpenRouterError(f"OpenRouter returned HTTP {response.status_code}.")
        try:
            completion = CompletionResponse.model_validate(response.json())
        except ValueError:
            raise OpenRouterError(
                "OpenRouter returned an invalid completion."
            ) from None

        choice = completion.choices[0]
        if choice.finish_reason in {"length", "error", "content_filter"}:
            raise OpenRouterError(
                f"OpenRouter stopped the completion ({choice.finish_reason})."
            )
        if not choice.message.tool_calls and not (choice.message.content or "").strip():
            raise OpenRouterError("OpenRouter returned an empty assistant turn.")
        return choice.message, ModelTelemetry(
            model=completion.model,
            provider=completion.provider,
            latency_ms=round((perf_counter() - start) * 1000, 2),
            usage=completion.usage,
        )
