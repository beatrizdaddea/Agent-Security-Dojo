from app.agent.executor import AgentExecutor
from app.attacks.attack_vectors import inject_attack
from app.attacks.injection_tasks import INJECTION_TASKS
from app.environment.seed_data import build_seed_state
from app.environment.workspace import Workspace
from app.evaluation.user_tasks import USER_TASKS


def test_vulnerable_mode_allows_attacker_influenced_write():
    workspace = Workspace(build_seed_state())
    injection = INJECTION_TASKS[0]
    inject_attack(workspace, injection)
    AgentExecutor().run(workspace, USER_TASKS[0], "vulnerable_mode", injection)
    assert any(email.recipient == "attacker@example.com" for email in workspace.state.sent_emails)


def test_secure_mode_blocks_exfiltration_to_attacker():
    workspace = Workspace(build_seed_state())
    injection = INJECTION_TASKS[0]
    inject_attack(workspace, injection)
    AgentExecutor().run(workspace, USER_TASKS[0], "secure_mode", injection)
    assert not any(email.recipient == "attacker@example.com" for email in workspace.state.sent_emails)


def test_secure_mode_blocks_sensitive_outgoing_content():
    workspace = Workspace(build_seed_state())
    task = USER_TASKS[3]
    from app.schemas.tool_calls import ToolCall
    from app.defenses.tool_call_guard import guard_tool_call

    call = ToolCall(
        tool_name="send_email",
        args={
            "to": "gerente@example.com",
            "subject": "segredo",
            "body": "CONFIDENTIAL token TEST-TOKEN",
        },
    )
    guarded = guard_tool_call(task, call, "secure_mode")
    assert not guarded.allowed


def test_secure_mode_permits_legitimate_authorized_write():
    workspace = Workspace(build_seed_state())
    AgentExecutor().run(workspace, USER_TASKS[3], "secure_mode")
    assert any(email.recipient == "gerente@example.com" for email in workspace.state.sent_emails)

