from app.agent.graph import run_agent
from app.environment.workspace import Workspace
from app.schemas.tasks import InjectionTask, UserTask


class AgentExecutor:
    def run(
        self,
        workspace: Workspace,
        task: UserTask,
        mode: str,
        injection: InjectionTask | None = None,
    ) -> str:
        result = run_agent(workspace, task, mode, injection)
        return str(result.get("answer", ""))

