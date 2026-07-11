from rich.console import Console

from app.agent.executor import AgentExecutor
from app.environment.seed_data import build_seed_state
from app.environment.workspace import Workspace
from app.evaluation.user_tasks import USER_TASKS


def main() -> None:
    console = Console()
    workspace = Workspace(build_seed_state())
    answer = AgentExecutor().run(workspace, USER_TASKS[0], "secure_mode")
    console.print("[bold]Agent Security Dojo[/bold]")
    console.print(f"Tarefa: {USER_TASKS[0].instruction}")
    console.print(f"Resposta: {answer}")
    console.print(f"Chamadas de ferramenta: {len(workspace.state.tool_logs)}")


if __name__ == "__main__":
    main()

