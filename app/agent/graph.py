from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agent.planner import execute_deterministic_plan
from app.environment.workspace import Workspace
from app.schemas.tasks import InjectionTask, UserTask
from app.tools.runtime import ToolRuntime


class AgentGraphState(TypedDict, total=False):
    workspace: Workspace
    task: UserTask
    mode: str
    injection: InjectionTask | None
    answer: str


def _pass(state: AgentGraphState) -> AgentGraphState:
    return state


def _execute_tool(state: AgentGraphState) -> AgentGraphState:
    runtime = ToolRuntime(
        workspace=state["workspace"],
        task=state["task"],
        mode=state["mode"],
        injection=state.get("injection"),
    )
    state["answer"] = execute_deterministic_plan(
        runtime, state["task"], state["mode"], state.get("injection")
    )
    return state


def build_agent_graph():
    graph = StateGraph(AgentGraphState)
    for node in [
        "load_user_task",
        "select_tools",
        "tool_filter",
        "plan_next_action",
        "inspect_tool_output",
        "apply_defenses",
        "decide_next_action",
        "tool_call_guard",
        "final_answer",
        "evaluate_result",
    ]:
        graph.add_node(node, _pass)
    graph.add_node("execute_tool", _execute_tool)
    graph.add_edge(START, "load_user_task")
    graph.add_edge("load_user_task", "select_tools")
    graph.add_edge("select_tools", "tool_filter")
    graph.add_edge("tool_filter", "plan_next_action")
    graph.add_edge("plan_next_action", "execute_tool")
    graph.add_edge("execute_tool", "inspect_tool_output")
    graph.add_edge("inspect_tool_output", "apply_defenses")
    graph.add_edge("apply_defenses", "decide_next_action")
    graph.add_edge("decide_next_action", "tool_call_guard")
    graph.add_edge("tool_call_guard", "final_answer")
    graph.add_edge("final_answer", "evaluate_result")
    graph.add_edge("evaluate_result", END)
    return graph.compile()


def run_agent(
    workspace: Workspace,
    task: UserTask,
    mode: str,
    injection: InjectionTask | None = None,
) -> dict[str, Any]:
    graph = build_agent_graph()
    return graph.invoke(
        {"workspace": workspace, "task": task, "mode": mode, "injection": injection}
    )

