from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, Field


class UserTask(BaseModel):
    id: str
    instruction: str
    expected_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    utility_check: str
    authorized_recipients: list[str] = Field(default_factory=list)
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

