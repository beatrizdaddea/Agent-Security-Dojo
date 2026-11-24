from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.tool_calls import ToolRequest


class TokenUsage(BaseModel):
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ModelTelemetry(BaseModel):
    model: str
    provider: str | None = None
    latency_ms: float
    usage: TokenUsage | None = None


class ProviderFunction(BaseModel):
    name: str
    arguments: str


class ProviderToolCall(BaseModel):
    id: str = Field(min_length=1)
    type: Literal["function"]
    function: ProviderFunction


class AssistantTurn(BaseModel):
    role: Literal["assistant"]
    content: str | None = None
    tool_calls: list[ProviderToolCall] | None = None

    def requests(self) -> list[ToolRequest]:
        return [
            ToolRequest(
                id=call.id, name=call.function.name, arguments=call.function.arguments
            )
            for call in self.tool_calls or []
        ]


class CompletionChoice(BaseModel):
    message: AssistantTurn
    finish_reason: str | None = None


class CompletionResponse(BaseModel):
    model: str
    provider: str | None = None
    choices: list[CompletionChoice] = Field(min_length=1)
    usage: TokenUsage | None = None
