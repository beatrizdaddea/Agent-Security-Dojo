import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.planner import plan_mock_action
from app.agent.prompts import system_prompt
from app.defenses.delimiters import wrap_untrusted_output
from app.defenses.injection_detector import detect_prompt_injection
from app.defenses.prompt_sandwich import sandwich_tool_output
from app.defenses.secret_protection import contains_protected_data
from app.defenses.tool_filter import select_allowed_tools, tool_definitions
from app.environment.workspace import Workspace
from app.evaluation.checks import check_utility
from app.llm.openrouter_client import OpenRouterClient, OpenRouterError
from app.schemas.messages import ModelTelemetry
from app.schemas.results import RunSummary
from app.schemas.tasks import InjectionTask, UserTask
from app.schemas.tool_calls import (
    PlannerMode,
    SecurityMode,
    ToolObservation,
    ToolRequest,
)
from app.tools.runtime import ToolRuntime

MAX_TURNS = 24
MAX_TOOL_CALLS = 24


class AgentGraphState(TypedDict, total=False):
    workspace: Workspace
    task: UserTask
    mode: SecurityMode
    planner_mode: PlannerMode
    client: OpenRouterClient | None
    injection: InjectionTask | None
    runtime: ToolRuntime
    tools: list[dict[str, Any]]
    messages: list[dict[str, Any]]
    pending: list[ToolRequest]
    observation: ToolObservation
    observations: list[ToolObservation]
    telemetry: list[ModelTelemetry]
    signals: dict[str, list[str]]
    turns: int
    proposed_answer: str
    status: str
    answer: str
    evaluation: RunSummary


def _load_user_task(state: AgentGraphState) -> AgentGraphState:
    task = state["task"].model_copy(deep=True)
    planner_mode = state.get("planner_mode", "mock")
    client = state.get("client")
    if planner_mode == "llm" and client is None:
        client = OpenRouterClient()
    return {
        "task": task,
        "planner_mode": planner_mode,
        "client": client,
        "runtime": ToolRuntime(state["workspace"], task, state["mode"]),
        "messages": [
            {"role": "system", "content": system_prompt(state["mode"])},
            {"role": "user", "content": task.instruction},
        ],
        "observations": [],
        "telemetry": [],
        "signals": {},
        "turns": 0,
        "status": "completed",
    }


def _select_tools(state: AgentGraphState) -> AgentGraphState:
    return {
        "tools": tool_definitions(select_allowed_tools(state["task"], state["mode"]))
    }


def _plan_next_action(state: AgentGraphState) -> AgentGraphState:
    if state["turns"] >= MAX_TURNS:
        return {"pending": [], "proposed_answer": "", "status": "turn_limit"}
    update: AgentGraphState = {"turns": state["turns"] + 1}
    if state["planner_mode"] == "mock":
        request, answer = plan_mock_action(
            state["task"], state["observations"], state.get("injection")
        )
        requests = [request] if request else []
    else:
        client = state["client"]
        if client is None:
            raise RuntimeError("The LLM planner has no client.")
        turn, telemetry = client.chat(state["messages"], state["tools"])
        requests, answer = turn.requests(), turn.content or ""
        update["messages"] = [*state["messages"], turn.model_dump(exclude_none=True)]
        update["telemetry"] = [*state["telemetry"], telemetry]

    prior_ids = {result.request_id for result in state["observations"]}
    request_ids = {request.id for request in requests}
    if prior_ids & request_ids or len(request_ids) != len(requests):
        raise OpenRouterError("Assistant returned duplicate tool call IDs.")
    if len(prior_ids) + len(requests) > MAX_TOOL_CALLS:
        return {
            **update,
            "pending": [],
            "proposed_answer": "",
            "status": "tool_call_limit",
        }
    return {**update, "pending": requests, "proposed_answer": answer}


def _tool_call_guard(state: AgentGraphState) -> AgentGraphState:
    request = state["pending"][0]
    source = "agent"
    if state["planner_mode"] == "mock" and request.id in {
        "fixture-read",
        "fixture-write",
    }:
        source = "untrusted_tool_output"
    state["runtime"].authorize(request, source=source)
    return {}


def _execute_tool(state: AgentGraphState) -> AgentGraphState:
    return {"observation": state["runtime"].execute()}


def _inspect_tool_output(state: AgentGraphState) -> AgentGraphState:
    observation = state["observation"]
    output = observation.model_dump(mode="json", include={"error", "value"})
    content = json.dumps(
        {"error": output["error"]}
        if observation.error
        else {"result": output["value"]},
        ensure_ascii=False,
    )
    signals = state["signals"]
    if observation.tainted:
        _, patterns = detect_prompt_injection(content)
        if patterns:
            signals = {**signals, observation.request_id: patterns}
        if state["mode"] == "secure_mode":
            content = content.replace("<", r"\u003c").replace(">", r"\u003e")
            content = sandwich_tool_output(
                wrap_untrusted_output(content), state["task"].instruction
            )
    messages = state["messages"]
    if state["planner_mode"] == "llm":
        messages = [
            *messages,
            {
                "role": "tool",
                "tool_call_id": observation.request_id,
                "content": content,
            },
        ]
    return {
        "observations": [*state["observations"], observation],
        "messages": messages,
        "signals": signals,
        "pending": state["pending"][1:],
    }


def _final_answer(state: AgentGraphState) -> AgentGraphState:
    if state["status"] != "completed":
        return {"answer": "A execução atingiu o limite de etapas."}
    answer = state["proposed_answer"]
    if state["mode"] == "secure_mode" and contains_protected_data(
        answer, state["workspace"].state.canaries
    ):
        return {
            "answer": "A resposta foi retida pela política de dados.",
            "status": "protected_data",
        }
    return {"answer": answer}


def _evaluate_result(state: AgentGraphState) -> AgentGraphState:
    calls = [observation.call for observation in state["observations"]]
    utility = state["status"] == "completed" and check_utility(
        state["task"], state["answer"], calls
    )
    return {
        "evaluation": RunSummary(
            status=state["status"],
            utility=utility,
            tool_attempts=len(calls),
            blocked_attempts=sum(not call.allowed for call in calls),
            tool_errors=sum(call.allowed and not call.executed for call in calls),
            tainted_outputs=sum(
                observation.tainted for observation in state["observations"]
            ),
            injection_signals=len(state["signals"]),
            model_turns=state["telemetry"],
        )
    }


def _after_plan(state: AgentGraphState) -> str:
    return "tool_call_guard" if state["pending"] else "final_answer"


def _after_inspection(state: AgentGraphState) -> str:
    return "tool_call_guard" if state["pending"] else "plan_next_action"


def build_agent_graph():
    graph = StateGraph(AgentGraphState)
    graph.add_node("load_user_task", _load_user_task)
    graph.add_node("select_tools", _select_tools)
    graph.add_node("plan_next_action", _plan_next_action)
    graph.add_node("tool_call_guard", _tool_call_guard)
    graph.add_node("execute_tool", _execute_tool)
    graph.add_node("inspect_tool_output", _inspect_tool_output)
    graph.add_node("final_answer", _final_answer)
    graph.add_node("evaluate_result", _evaluate_result)
    graph.add_edge(START, "load_user_task")
    graph.add_edge("load_user_task", "select_tools")
    graph.add_edge("select_tools", "plan_next_action")
    graph.add_conditional_edges(
        "plan_next_action", _after_plan, ["tool_call_guard", "final_answer"]
    )
    graph.add_edge("tool_call_guard", "execute_tool")
    graph.add_edge("execute_tool", "inspect_tool_output")
    graph.add_conditional_edges(
        "inspect_tool_output",
        _after_inspection,
        ["tool_call_guard", "plan_next_action"],
    )
    graph.add_edge("final_answer", "evaluate_result")
    graph.add_edge("evaluate_result", END)
    return graph.compile()


def run_agent(
    workspace: Workspace,
    task: UserTask,
    mode: SecurityMode,
    injection: InjectionTask | None = None,
    *,
    planner_mode: PlannerMode = "mock",
    client: OpenRouterClient | None = None,
) -> AgentGraphState:
    if planner_mode not in {"mock", "llm"}:
        raise ValueError("Unknown planner mode")
    return build_agent_graph().invoke(
        {
            "workspace": workspace,
            "task": task,
            "mode": mode,
            "planner_mode": planner_mode,
            "client": client,
            "injection": injection if planner_mode == "mock" else None,
        },
        config={"recursion_limit": 4 * (MAX_TURNS + MAX_TOOL_CALLS) + 10},
    )
