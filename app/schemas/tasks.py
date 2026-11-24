from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.tool_calls import CalendarEventArgs


class UserTask(BaseModel):
    id: str
    instruction: str
    expected_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    utility_check: str
    authorized_recipients: list[str] = Field(default_factory=list)
    authorized_documents: list[str] = Field(default_factory=list)
    authorized_calendar_date: str | None = None
    authorized_event: CalendarEventArgs | None = None
    task_type: Literal[
        "summarize_emails",
        "list_calendar",
        "summarize_document",
        "send_authorized_summary",
        "create_authorized_event",
    ]


class InjectionTask(BaseModel):
    id: str
    attacker_goal: str
    target_tool: str
    security_check: str
    attack_vector: Literal["email_body", "calendar_description", "document_content"]
    payload: str


SecurityCheck = Callable[[object], bool]
