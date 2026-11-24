from collections import Counter

import pytest

from app.agent.graph import build_agent_graph, run_agent
from app.attacks.attack_vectors import inject_attack
from app.attacks.injection_tasks import INJECTION_TASKS
from app.environment.seed_data import build_seed_state
from app.environment.state import Document
from app.environment.workspace import Workspace
from app.evaluation.user_tasks import USER_TASKS
from app.tools.runtime import ToolRuntime

APPROVED = "contas@alpine-ledger.example"


def test_langgraph_runs_each_stage_and_loops_before_evaluating():
    workspace = Workspace(build_seed_state())
    injection = INJECTION_TASKS[0]
    inject_attack(workspace, injection)
    updates = list(
        build_agent_graph().stream(
            {
                "workspace": workspace,
                "task": USER_TASKS[0],
                "mode": "secure_mode",
                "injection": injection,
            },
            config={"recursion_limit": 100},
        )
    )
    stages = [node for step in updates for node in step]
    assert stages[:3] == ["load_user_task", "select_tools", "plan_next_action"]
    assert stages[-2:] == ["final_answer", "evaluate_result"]
    counts = Counter(stages)
    assert (
        counts["tool_call_guard"]
        == counts["execute_tool"]
        == counts["inspect_tool_output"]
        == 5
    )
    assert counts["plan_next_action"] == 6
    assert updates[-1]["evaluate_result"]["evaluation"].utility
    assert workspace.state.sent_emails == []
    assert workspace.state.tool_logs[-1].reason == "TOOL_OUT_OF_SCOPE"
    assert workspace.state.tool_logs[-1].taint_sources


def test_existing_fixture_changes_only_the_vulnerable_workspace():
    workspace = Workspace(build_seed_state())
    injection = INJECTION_TASKS[0]
    inject_attack(workspace, injection)
    result = run_agent(workspace, USER_TASKS[0], "vulnerable_mode", injection)
    assert result["evaluation"].utility
    assert result["evaluation"].tainted_outputs
    assert result["evaluation"].model_turns == []
    assert len(workspace.state.sent_emails) == 1


@pytest.fixture
def email_runtime():
    task = USER_TASKS[3].model_copy(update={"authorized_recipients": [APPROVED]})
    return ToolRuntime(Workspace(build_seed_state()), task, "secure_mode")


@pytest.mark.parametrize(
    "destination",
    [
        "entregas@north-quay.example",
        f"{APPROVED}, copies@mountain-mail.example",
        f"Finance <{APPROVED}>",
    ],
)
def test_unapproved_recipients_are_denied_regardless_of_text(
    email_runtime, destination
):
    email_runtime.call("search_emails", query="*")
    result = email_runtime.call(
        "send_email",
        to=destination,
        subject="Mapa das obras",
        body="Revisão da margem leste.",
    )
    assert result is None
    log = email_runtime.workspace.state.tool_logs[-1]
    assert log.taint_sources
    assert log.reason == "HUMAN_APPROVAL_REQUIRED"
    assert email_runtime.workspace.state.sent_emails == []


@pytest.mark.parametrize(
    "body",
    [
        "The password policy and token rotation schedule are on the meeting agenda.",
        "Password: rotating credentials is recommended.",
        "Delete old calendar invitations after the audit. This is a document excerpt.",
        "As regras de informações confidenciais constam na pauta.",
    ],
)
def test_heuristic_matches_do_not_control_the_authorized_summary(email_runtime, body):
    email_runtime.workspace.state.inbox[-1].body = body
    email_runtime.call("search_emails", query="*")
    result = email_runtime.call("send_email", to=APPROVED, subject="Resumo", body=body)
    assert result.body == body
    log = email_runtime.workspace.state.tool_logs[-1]
    assert log.taint_sources and log.executed


@pytest.mark.parametrize("field", ["subject", "body"])
def test_dynamic_canaries_are_blocked_for_authorized_recipients(email_runtime, field):
    args = {"to": APPROVED, "subject": "Resumo", "body": "Revisão"}
    args[field] += " " + email_runtime.workspace.state.canaries[0].upper()
    assert email_runtime.call("send_email", **args) is None
    assert email_runtime.workspace.state.tool_logs[-1].reason == "PROTECTED_DATA"


def test_generic_secret_format_blocks_private_keys(email_runtime):
    body = "-----BEGIN PRIVATE KEY-----\nExample data."
    assert (
        email_runtime.call("send_email", to=APPROVED, subject="Resumo", body=body)
        is None
    )
    assert email_runtime.workspace.state.tool_logs[-1].reason == "PROTECTED_DATA"


def test_authorized_summary_is_a_single_write(email_runtime):
    args = {"to": APPROVED, "subject": "Resumo", "body": "Entregas em dia"}
    assert email_runtime.call("send_email", **args) is not None
    assert email_runtime.call("send_email", **args) is None
    assert (
        email_runtime.workspace.state.tool_logs[-1].reason == "WRITE_ALREADY_COMPLETED"
    )


@pytest.mark.parametrize(
    "extra_args",
    [
        {"title": "Design review for graphite valves"},
        {"date": "2026-07-01 10:30"},
        {"participants": ["ana@example.com", "facilities@somewhere-else.example"]},
        {"description": "Bring portfolio for review."},
    ],
)
def test_event_requires_exact_authorized_arguments(extra_args):
    task = USER_TASKS[4]
    runtime = ToolRuntime(Workspace(build_seed_state()), task, "secure_mode")
    args = task.authorized_event.model_dump()
    assert runtime.call("create_calendar_event", **(args | extra_args)) is None
    assert runtime.workspace.state.tool_logs[-1].reason == "HUMAN_APPROVAL_REQUIRED"
    assert (
        runtime.call("create_calendar_event", source="untrusted_tool_output", **args)
        is None
    )
    assert runtime.workspace.state.tool_logs[-1].reason == "HUMAN_APPROVAL_REQUIRED"
    assert runtime.call("create_calendar_event", **args) is not None


def test_missing_write_authorization_fails_closed(email_runtime):
    task = USER_TASKS[3].model_copy(update={"authorized_recipients": []})
    runtime = ToolRuntime(email_runtime.workspace, task, "secure_mode")
    assert (
        runtime.call(
            "send_email", to=APPROVED, subject="Resumo", body="Notas de manutenção"
        )
        is None
    )
    assert runtime.workspace.state.tool_logs[-1].reason == "HUMAN_APPROVAL_REQUIRED"


def test_secure_drive_scope_and_unregistered_workspace_methods():
    workspace = Workspace(build_seed_state())
    workspace.state.drive.append(
        Document(id="doc-3", name="payroll.csv", content="synthetic")
    )
    runtime = ToolRuntime(workspace, USER_TASKS[2], "secure_mode")
    assert runtime.call("read_document", document_name="payroll.csv") is None
    assert workspace.state.tool_logs[-1].reason == "DOCUMENT_OUT_OF_SCOPE"
    assert [doc.name for doc in runtime.call("search_drive", query="*")] == [
        "relatorio.txt"
    ]
    for mode in ["vulnerable_mode", "secure_mode"]:
        runtime = ToolRuntime(workspace, USER_TASKS[2], mode)
        assert runtime.call("clone") is None
        assert workspace.state.tool_logs[-1].reason == "UNKNOWN_TOOL"
