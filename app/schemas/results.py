from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    task_id: str
    injection_id: str
    mode: str
    benign_utility: float
    utility_under_attack: float
    targeted_attack_success: bool
    blocked_tool_calls: int = 0
    unsafe_tool_calls: int = 0
    false_positive_blocks: int = 0
    false_negative_allows: int = 0
    legitimate_write_attempts: int = 0
    malicious_write_attempts: int = 0
    notes: str = ""

