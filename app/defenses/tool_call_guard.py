from app.defenses.secret_protection import contains_protected_data
from app.defenses.tool_filter import WRITE_TOOLS, is_tool_allowed
from app.schemas.tasks import UserTask
from app.schemas.tool_calls import ToolCall

HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"


def guard_tool_call(
    task: UserTask,
    call: ToolCall,
    mode: str,
    *,
    canaries: tuple[str, ...] = (),
    write_completed: bool = False,
) -> ToolCall:
    if not is_tool_allowed(task, call.tool_name, mode):
        return call.model_copy(update={"allowed": False, "reason": "TOOL_OUT_OF_SCOPE"})
    if mode == "vulnerable_mode":
        return call

    if (
        call.tool_name == "read_document"
        and call.args.get("document_name") not in task.authorized_documents
    ):
        return call.model_copy(
            update={"allowed": False, "reason": "DOCUMENT_OUT_OF_SCOPE"}
        )
    if call.tool_name == "list_calendar_events" and (
        not task.authorized_calendar_date
        or call.args.get("date") != task.authorized_calendar_date
    ):
        return call.model_copy(update={"allowed": False, "reason": "DATE_OUT_OF_SCOPE"})
    if call.tool_name not in WRITE_TOOLS:
        return call

    denial = _write_denial(task, call, canaries, write_completed)
    if denial:
        return call.model_copy(
            update={"allowed": False, "reason": denial, "risk_level": "high"}
        )
    return call


def _write_denial(
    task: UserTask, call: ToolCall, canaries: tuple[str, ...], write_completed: bool
) -> str:
    if call.tool_name == "send_email" and task.task_type == "send_authorized_summary":
        if call.args.get("to") not in task.authorized_recipients:
            return HUMAN_APPROVAL_REQUIRED
        subject, body = call.args.get("subject"), call.args.get("body")
        if not isinstance(subject, str) or not isinstance(body, str):
            return "INVALID_ARGUMENTS"
        if not subject.strip() or not body.strip():
            return "INVALID_ARGUMENTS"
        if contains_protected_data(subject, canaries) or contains_protected_data(
            body, canaries
        ):
            return "PROTECTED_DATA"
        return "WRITE_ALREADY_COMPLETED" if write_completed else ""
    if call.tool_name == "create_calendar_event" and task.authorized_event:
        tainted = call.taint_sources or call.source == "untrusted_tool_output"
        if not tainted and call.args == task.authorized_event.model_dump():
            if contains_protected_data(
                task.authorized_event.title, canaries
            ) or contains_protected_data(task.authorized_event.description, canaries):
                return "PROTECTED_DATA"
            return "WRITE_ALREADY_COMPLETED" if write_completed else ""
    return HUMAN_APPROVAL_REQUIRED
