from app.defenses.tool_filter import is_tool_allowed, select_allowed_tools
from app.evaluation.user_tasks import USER_TASKS


def test_email_summary_allows_only_email_read_tools_in_secure_mode():
    task = USER_TASKS[0]
    assert select_allowed_tools(task, "secure_mode") == {"search_emails", "read_email"}
    assert not is_tool_allowed(task, "send_email", "secure_mode")


def test_calendar_listing_blocks_write_tools():
    task = USER_TASKS[1]
    assert is_tool_allowed(task, "list_calendar_events", "secure_mode")
    assert not is_tool_allowed(task, "create_calendar_event", "secure_mode")


def test_authorized_email_task_allows_send_email():
    task = USER_TASKS[3]
    assert is_tool_allowed(task, "send_email", "secure_mode")
    assert not is_tool_allowed(task, "delete_document", "secure_mode")

