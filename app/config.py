import math
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = field(repr=False)
    openrouter_model: str
    openrouter_timeout_seconds: float

    @classmethod
    def from_env(cls, model: str | None = None) -> "Settings":
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ValueError("Set OPENROUTER_API_KEY to use --mode llm.")
        selected_model = (model or os.getenv("OPENROUTER_MODEL", "")).strip()
        try:
            timeout = float(os.getenv("OPENROUTER_TIMEOUT_SECONDS", "30"))
        except ValueError:
            raise ValueError(
                "OPENROUTER_TIMEOUT_SECONDS must be a positive number."
            ) from None
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError(
                "OPENROUTER_TIMEOUT_SECONDS must be a positive finite number."
            )
        return cls(api_key, selected_model or DEFAULT_OPENROUTER_MODEL, timeout)
