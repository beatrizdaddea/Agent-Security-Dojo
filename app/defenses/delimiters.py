UNTRUSTED_OPEN = "<UNTRUSTED_TOOL_OUTPUT>"
UNTRUSTED_CLOSE = "</UNTRUSTED_TOOL_OUTPUT>"


def wrap_untrusted_output(text: str) -> str:
    return f"{UNTRUSTED_OPEN}\n{text}\n{UNTRUSTED_CLOSE}"

