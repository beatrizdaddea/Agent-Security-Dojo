from app.agent.graph import run_agent
from app.environment.workspace import Workspace
from app.llm.openrouter_client import OpenRouterClient
from app.schemas.tasks import InjectionTask, UserTask
from app.schemas.tool_calls import PlannerMode, SecurityMode


class AgentExecutor:
    def run(
        self,
        workspace: Workspace,
        task: UserTask,
        mode: SecurityMode,
        injection: InjectionTask | None = None,
        *,
        planner_mode: PlannerMode = "mock",
        client: OpenRouterClient | None = None,
    ) -> str:
        return run_agent(
            workspace, task, mode, injection, planner_mode=planner_mode, client=client
        )["answer"]
