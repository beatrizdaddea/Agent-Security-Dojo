from app.schemas.tasks import UserTask


READ_TOOLS = {
    "search_emails",
    "read_email",
    "list_calendar_events",
    "read_document",
    "search_drive",
}
WRITE_TOOLS = {"send_email", "create_calendar_event", "delete_document"}
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
    return set(TASK_ALLOWED_TOOLS[task.task_type])


def is_tool_allowed(task: UserTask, tool_name: str, mode: str) -> bool:
    return tool_name in select_allowed_tools(task, mode)

