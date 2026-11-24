import argparse
import json
import re
from collections import Counter
from pathlib import Path
from tempfile import NamedTemporaryFile

from rich.console import Console
from rich.table import Table

from app.agent.graph import run_agent
from app.attacks.attack_vectors import inject_attack, observed_fixture
from app.attacks.injection_tasks import INJECTION_TASKS
from app.defenses.tool_filter import WRITE_TOOLS
from app.environment.seed_data import build_seed_state
from app.environment.workspace import Workspace
from app.evaluation.checks import check_attack_success, label_attempts
from app.evaluation.metrics import aggregate_metrics
from app.evaluation.user_tasks import USER_TASKS
from app.llm.openrouter_client import OpenRouterClient, OpenRouterError
from app.schemas.results import EvaluationResult
from app.schemas.tasks import InjectionTask, UserTask
from app.schemas.tool_calls import PlannerMode, SecurityMode

SCENARIOS = [
    (USER_TASKS[0], INJECTION_TASKS[0]),
    (USER_TASKS[1], INJECTION_TASKS[1]),
    (USER_TASKS[2], INJECTION_TASKS[2]),
    (USER_TASKS[3], INJECTION_TASKS[3]),
    (USER_TASKS[4], INJECTION_TASKS[1]),
]
MODES: dict[str, SecurityMode] = {
    "vulnerable": "vulnerable_mode",
    "defensive": "secure_mode",
}


class EvaluationEngine:
    def __init__(
        self, planner_mode: PlannerMode = "mock", model: str | None = None
    ) -> None:
        self.planner_mode = planner_mode
        self.client = OpenRouterClient(model) if planner_mode == "llm" else None

    def run_scenario(
        self, task: UserTask, injection: InjectionTask, mode: SecurityMode
    ) -> EvaluationResult:
        clean = Workspace(build_seed_state())
        attacked = clean.clone()
        inject_attack(attacked, injection)

        benign_run = run_agent(
            clean, task, mode, planner_mode=self.planner_mode, client=self.client
        )
        attacked_run = run_agent(
            attacked,
            task,
            mode,
            injection,
            planner_mode=self.planner_mode,
            client=self.client,
        )
        logs = attacked.state.tool_logs
        attack_success = check_attack_success(injection, attacked)
        attacked_labels = label_attempts(
            task, attacked_run["observations"], attacked.state.canaries
        )
        clean_labels = label_attempts(
            task, benign_run["observations"], clean.state.canaries
        )
        labeled_writes = [
            (call, in_scope)
            for call, in_scope in [*clean_labels, *attacked_labels]
            if call.tool_name in WRITE_TOOLS
        ]

        return EvaluationResult(
            task_id=task.id,
            injection_id=injection.id,
            mode=mode,
            benign_utility=float(benign_run["evaluation"].utility),
            utility_under_attack=float(attacked_run["evaluation"].utility),
            targeted_attack_success=attack_success,
            attack_fixture_observed=observed_fixture(
                injection, attacked_run["observations"]
            ),
            total_tool_calls=len(logs),
            blocked_tool_calls=sum(not call.allowed for call in logs),
            unsafe_tool_calls=sum(
                call.executed and not in_scope for call, in_scope in attacked_labels
            ),
            false_positive_blocks=sum(
                not call.allowed and in_scope for call, in_scope in labeled_writes
            ),
            false_negative_allows=sum(
                call.allowed and not in_scope for call, in_scope in labeled_writes
            ),
            legitimate_write_attempts=sum(in_scope for _, in_scope in labeled_writes),
            malicious_write_attempts=sum(
                not in_scope for _, in_scope in labeled_writes
            ),
            tool_denials=dict(
                Counter(call.reason for call in logs if not call.allowed)
            ),
            benign_run=benign_run["evaluation"],
            attacked_run=attacked_run["evaluation"],
        )

    def run(self, mode: SecurityMode) -> list[EvaluationResult]:
        return [
            self.run_scenario(task, injection, mode) for task, injection in SCENARIOS
        ]


def _write_artifact(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file = NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False)
    temp = Path(file.name)
    try:
        with file:
            json.dump(report, file, indent=2, ensure_ascii=False)
            file.write("\n")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def _print_metrics(metrics: dict[str, dict[str, float | None]]) -> None:
    table = Table(title="Agent Security Dojo benchmark")
    table.add_column("Metric")
    for name in metrics:
        table.add_column(name, justify="right")
    for metric in metrics["vulnerable"]:
        table.add_row(
            metric,
            *[
                "n/a" if values[metric] is None else str(values[metric])
                for values in metrics.values()
            ],
        )
    Console().print(table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark the synthetic workspace.")
    parser.add_argument("--mode", choices=["mock", "llm"], default="mock")
    parser.add_argument("--model", help="Override OPENROUTER_MODEL for --mode llm.")
    args = parser.parse_args()
    if args.model is not None and args.mode == "mock":
        parser.error("--model requires --mode llm.")
    try:
        engine = EvaluationEngine(args.mode, args.model)
        results = {name: engine.run(mode) for name, mode in MODES.items()}
    except (OpenRouterError, ValueError) as error:
        parser.exit(1, f"{error}\n")

    model = engine.client.model if engine.client else None
    model_slug = re.sub(r"[^A-Za-z0-9._-]", "_", model) if model else None
    artifact_name = (
        f"llm_benchmark_{model_slug}.json" if model else "mock_benchmark.json"
    )
    path = Path("results") / artifact_name
    metrics = {name: aggregate_metrics(rows) for name, rows in results.items()}
    _write_artifact(
        path,
        {
            "schema_version": 1,
            "planner_mode": args.mode,
            "model": model,
            "scenarios_per_mode": len(SCENARIOS),
            "metrics": metrics,
            "scenarios": {
                name: [row.model_dump(mode="json") for row in rows]
                for name, rows in results.items()
            },
        },
    )
    _print_metrics(metrics)
    Console().print(f"Saved {path}")


if __name__ == "__main__":
    main()
