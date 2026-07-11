from app.tools.runtime import ToolRuntime


def list_calendar_events(runtime: ToolRuntime, date: str):
    return runtime.call("list_calendar_events", date=date)


def create_calendar_event(
    runtime: ToolRuntime,
    title: str,
    date: str,
    participants: list[str],
    description: str,
    source: str = "agent",
):
    return runtime.call(
        "create_calendar_event",
        source=source,
        title=title,
        date=date,
        participants=participants,
        description=description,
    )

