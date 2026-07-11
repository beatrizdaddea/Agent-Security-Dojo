from app.evaluation.metrics import aggregate_metrics
from app.schemas.results import EvaluationResult


def test_aggregate_metrics_formulas():
    results = [
        EvaluationResult(
            task_id="a",
            injection_id="x",
            mode="secure_mode",
            benign_utility=1.0,
            utility_under_attack=1.0,
            targeted_attack_success=False,
            blocked_tool_calls=1,
            unsafe_tool_calls=0,
            false_positive_blocks=0,
            false_negative_allows=0,
            legitimate_write_attempts=1,
            malicious_write_attempts=1,
        ),
        EvaluationResult(
            task_id="b",
            injection_id="y",
            mode="vulnerable_mode",
            benign_utility=1.0,
            utility_under_attack=0.0,
            targeted_attack_success=True,
            blocked_tool_calls=0,
            unsafe_tool_calls=1,
            false_positive_blocks=0,
            false_negative_allows=1,
            legitimate_write_attempts=0,
            malicious_write_attempts=1,
        ),
    ]
    metrics = aggregate_metrics(results)
    assert metrics["benign_utility"] == 1.0
    assert metrics["utility_under_attack"] == 0.5
    assert metrics["targeted_attack_success_rate"] == 0.5
    assert metrics["false_negative_rate"] == 0.5

