from typing import Any

from pydantic import BaseModel, Field

from app.schemas.tool_calls import ToolCall


class Email(BaseModel):
    id: str
    sender: str
    recipient: str
    subject: str
    body: str
    is_untrusted: bool = False


class CalendarEvent(BaseModel):
    id: str
    title: str
    date: str
    description: str
    participants: list[str] = Field(default_factory=list)
    is_untrusted: bool = False


class Document(BaseModel):
    id: str
    name: str
    content: str
    is_untrusted: bool = False


class WorkspaceState(BaseModel):
    canaries: tuple[str, ...] = ()
    inbox: list[Email] = Field(default_factory=list)
    calendar: list[CalendarEvent] = Field(default_factory=list)
    drive: list[Document] = Field(default_factory=list)
    sent_emails: list[Email] = Field(default_factory=list)
    tool_logs: list[ToolCall] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
