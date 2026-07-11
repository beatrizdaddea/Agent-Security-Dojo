from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "critical"]


class ToolCall(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    allowed: bool = True
    reason: str = ""
    source: str = "agent"
    risk_level: RiskLevel = "low"

