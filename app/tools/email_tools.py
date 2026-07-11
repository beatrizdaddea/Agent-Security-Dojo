from app.tools.runtime import ToolRuntime


def search_emails(runtime: ToolRuntime, query: str):
    return runtime.call("search_emails", query=query)


def read_email(runtime: ToolRuntime, email_id: str):
    return runtime.call("read_email", email_id=email_id)


def send_email(runtime: ToolRuntime, to: str, subject: str, body: str, source: str = "agent"):
    return runtime.call("send_email", source=source, to=to, subject=subject, body=body)

