from app.schemas.tasks import UserTask
from app.schemas.tool_calls import (
    CalendarDateArgs,
    CalendarEventArgs,
    DocumentArgs,
    QueryArgs,
    ReadEmailArgs,
    SendEmailArgs,
    ToolArguments,
)

READ_TOOLS: dict[str, type[ToolArguments]] = {
    "search_emails": QueryArgs,
    "read_email": ReadEmailArgs,
    "list_calendar_events": CalendarDateArgs,
    "read_document": DocumentArgs,
    "search_drive": QueryArgs,
}
WRITE_TOOLS: dict[str, type[ToolArguments]] = {
    "send_email": SendEmailArgs,
    "create_calendar_event": CalendarEventArgs,
    "delete_document": DocumentArgs,
}
ALL_TOOLS = READ_TOOLS | WRITE_TOOLS


TASK_ALLOWED_TOOLS = {
    "summarize_emails": {"search_emails", "read_email"},
    "list_calendar": {"list_calendar_events"},
    "summarize_document": {"read_document", "search_drive"},
    "send_authorized_summary": {"search_emails", "read_email", "send_email"},
    "create_authorized_event": {"create_calendar_event"},
}


def select_allowed_tools(task: UserTask, mode: str) -> set[str]:
    if mode == "vulnerable_mode":
        return set(ALL_TOOLS)
    if mode == "secure_mode":
        return set(TASK_ALLOWED_TOOLS.get(task.task_type, ()))
    raise ValueError("Unknown security mode")


def is_tool_allowed(task: UserTask, tool_name: str, mode: str) -> bool:
    return tool_name in select_allowed_tools(task, mode)


def tool_definitions(names: set[str]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "parameters": ALL_TOOLS[name].model_json_schema(),
            },
        }
        for name in sorted(names)
    ]
