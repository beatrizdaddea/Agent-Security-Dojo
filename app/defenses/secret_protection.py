import re

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,})\b"),
)
CREDENTIAL_ASSIGNMENT = re.compile(
    r"\b(?:api[_ -]?key|access[_ -]?token|password)\s*[:=]\s*"
    r"""['"]?([A-Za-z0-9_./+@!$%=-]{8,})""",
    re.IGNORECASE,
)


def contains_protected_data(text: str, canaries: tuple[str, ...] = ()) -> bool:
    folded = text.casefold()
    if any(value.casefold() in folded for value in canaries if value):
        return True
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        return True
    return any(
        any(char.isdigit() or char in "_+@!$%=" for char in match.group(1))
        for match in CREDENTIAL_ASSIGNMENT.finditer(text)
    )
