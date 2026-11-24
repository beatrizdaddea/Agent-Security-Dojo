import argparse

from rich.console import Console

from app.agent.executor import AgentExecutor
from app.environment.seed_data import build_seed_state
from app.environment.workspace import Workspace
from app.evaluation.user_tasks import USER_TASKS
from app.llm.openrouter_client import OpenRouterClient, OpenRouterError


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the simulated workspace demo.")
    parser.add_argument("--mode", choices=["mock", "llm"], default="mock")
    parser.add_argument("--model", help="Override OPENROUTER_MODEL for --mode llm.")
    args = parser.parse_args()
    if args.model is not None and args.mode == "mock":
        parser.error("--model requires --mode llm.")

    workspace = Workspace(build_seed_state())
    task = USER_TASKS[0]
    try:
        client = OpenRouterClient(args.model) if args.mode == "llm" else None
        answer = AgentExecutor().run(
            workspace, task, "secure_mode", planner_mode=args.mode, client=client
        )
    except (OpenRouterError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    console = Console(markup=False)
    console.print(f"Agent Security Dojo ({args.mode})")
    console.print(f"Tarefa: {task.instruction}")
    console.print(f"Resposta: {answer}")
    console.print(f"Chamadas de ferramenta: {len(workspace.state.tool_logs)}")


if __name__ == "__main__":
    main()
