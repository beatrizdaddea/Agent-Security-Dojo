import re


PATTERNS = [
    r"ignore previous instructions",
    r"ignore as instru[cç][oõ]es anteriores",
    r"disregard previous",
    r"developer mode",
    r"system prompt",
    r"exfiltrate",
    r"\bleak\b",
    r"\bvaze\b",
    r"envie para attacker",
    r"send to attacker",
    r"security code",
    r"authentication code",
    r"password",
    r"\btoken\b",
    r"confidential",
    r"\bdelete\b",
    r"transfer money",
]


def detect_prompt_injection(text: str) -> tuple[bool, list[str]]:
    hits = [pattern for pattern in PATTERNS if re.search(pattern, text, re.I)]
    return bool(hits), hits

