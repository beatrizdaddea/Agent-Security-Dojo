from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["low", "medium", "high", "critical"]
SecurityMode = Literal["vulnerable_mode", "secure_mode"]
PlannerMode = Literal["mock", "llm"]


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class QueryArgs(ToolArguments):
    query: str = Field(
        description="Text to search for. Use * to list all scoped records."
    )


class ReadEmailArgs(ToolArguments):
    email_id: str


class CalendarDateArgs(ToolArguments):
    date: str = Field(description="Date as YYYY-MM-DD.")


class DocumentArgs(ToolArguments):
    document_name: str


class SendEmailArgs(ToolArguments):
    to: str
    subject: str
    body: str


class CalendarEventArgs(ToolArguments):
    title: str
    date: str = Field(description="Date and time as YYYY-MM-DD HH:MM.")
    participants: list[str]
    description: str = Field(
        description="Use an empty string if no description was requested."
    )


class ToolRequest(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] | str


class ToolCall(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    allowed: bool = True
    executed: bool = False
    reason: str = ""
    source: str = "agent"
    taint_sources: tuple[str, ...] = ()
    risk_level: RiskLevel = "low"


class ToolObservation(BaseModel):
    request_id: str
    call: ToolCall
    value: Any = None
    error: str = ""
    tainted: bool = False
