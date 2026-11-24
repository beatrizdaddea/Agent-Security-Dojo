from pydantic import BaseModel, Field

from app.schemas.messages import ModelTelemetry


class RunSummary(BaseModel):
    status: str
    utility: bool
    tool_attempts: int
    blocked_attempts: int
    tool_errors: int
    tainted_outputs: int
    injection_signals: int
    model_turns: list[ModelTelemetry] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    task_id: str
    injection_id: str
    mode: str
    benign_utility: float
    utility_under_attack: float
    targeted_attack_success: bool
    attack_fixture_observed: bool = False
    total_tool_calls: int = 0
    blocked_tool_calls: int = 0
    unsafe_tool_calls: int = 0
    false_positive_blocks: int = 0
    false_negative_allows: int = 0
    legitimate_write_attempts: int = 0
    malicious_write_attempts: int = 0
    tool_denials: dict[str, int] = Field(default_factory=dict)
    benign_run: RunSummary | None = None
    attacked_run: RunSummary | None = None
