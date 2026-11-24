from copy import deepcopy

from app.environment.state import CalendarEvent, Document, Email, WorkspaceState
from app.schemas.tool_calls import ToolCall


class Workspace:
    """Ambiente local mutavel; nenhuma ferramenta fala com servicos externos."""

    def __init__(self, state: WorkspaceState):
        self.state = state

    def clone(self) -> "Workspace":
        return Workspace(deepcopy(self.state))

    def log_tool_call(self, call: ToolCall) -> None:
        self.state.tool_logs.append(call)

    def search_emails(self, query: str) -> list[Email]:
        q = query.lower()
        return [
            email
            for email in self.state.inbox
            if q in email.subject.lower() or q in email.body.lower() or query == "*"
        ]

    def read_email(self, email_id: str) -> Email:
        for email in self.state.inbox:
            if email.id == email_id:
                return email
        raise KeyError(f"Email nao encontrado: {email_id}")

    def list_calendar_events(self, date: str) -> list[CalendarEvent]:
        return [event for event in self.state.calendar if event.date.startswith(date)]

    def read_document(self, document_name: str) -> Document:
        for document in self.state.drive:
            if document.name == document_name:
                return document
        raise KeyError(f"Documento nao encontrado: {document_name}")

    def search_drive(
        self, query: str, *, allowed_names: list[str] | None = None
    ) -> list[Document]:
        q = query.lower()
        return [
            document
            for document in self.state.drive
            if (allowed_names is None or document.name in allowed_names)
            and (
                q in document.name.lower()
                or q in document.content.lower()
                or query == "*"
            )
        ]

    def send_email(self, to: str, subject: str, body: str) -> Email:
        email = Email(
            id=f"sent-{len(self.state.sent_emails) + 1}",
            sender="usuario@example.com",
            recipient=to,
            subject=subject,
            body=body,
            is_untrusted=False,
        )
        self.state.sent_emails.append(email)
        return email

    def create_calendar_event(
        self, title: str, date: str, participants: list[str], description: str
    ) -> CalendarEvent:
        event = CalendarEvent(
            id=f"created-{len(self.state.calendar) + 1}",
            title=title,
            date=date,
            participants=participants,
            description=description,
            is_untrusted=False,
        )
        self.state.calendar.append(event)
        return event

    def delete_document(self, document_name: str) -> bool:
        before = len(self.state.drive)
        self.state.drive = [
            document for document in self.state.drive if document.name != document_name
        ]
        return len(self.state.drive) < before
