from app.evaluation.evaluator import EvaluationEngine
from app.evaluation.metrics import aggregate_metrics
from app.schemas.results import EvaluationResult


def test_metric_denominators_and_empty_cohorts():
    rows = [
        EvaluationResult(
            task_id="a",
            injection_id="x",
            mode="secure_mode",
            benign_utility=1.0,
            utility_under_attack=1.0,
            targeted_attack_success=False,
            total_tool_calls=10,
            blocked_tool_calls=2,
            unsafe_tool_calls=1,
            false_positive_blocks=1,
            false_negative_allows=1,
            legitimate_write_attempts=4,
            malicious_write_attempts=2,
        ),
    ]
    assert aggregate_metrics(rows) == {
        "benign_utility": 1.0,
        "utility_under_attack": 1.0,
        "targeted_attack_success_rate": 0.0,
        "tool_misuse_rate": 0.1,
        "blocked_tool_call_rate": 0.2,
        "false_positive_rate": 0.25,
        "false_negative_rate": 0.5,
    }
    assert all(value is None for value in aggregate_metrics([]).values())


def test_mock_suite_has_four_exposed_fixtures_and_one_no_exposure_control():
    engine = EvaluationEngine()
    for mode, expected_successes in [("vulnerable_mode", 4), ("secure_mode", 0)]:
        rows = engine.run(mode)
        assert len(rows) == 5
        assert sum(row.attack_fixture_observed for row in rows) == 4
        assert sum(row.targeted_attack_success for row in rows) == expected_successes
        assert all(
            row.benign_utility == row.utility_under_attack == 1.0 for row in rows
        )
        assert all(
            row.benign_run.model_turns == row.attacked_run.model_turns == []
            for row in rows
        )
