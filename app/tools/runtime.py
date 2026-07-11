from typing import Any

from app.defenses.tool_call_guard import guard_tool_call, is_write_tool
from app.defenses.tool_filter import is_tool_allowed
from app.environment.workspace import Workspace
from app.schemas.tasks import InjectionTask, UserTask
from app.schemas.tool_calls import ToolCall


class ToolRuntime:
    def __init__(
        self,
        workspace: Workspace,
        task: UserTask,
        mode: str,
        injection: InjectionTask | None = None,
    ):
        self.workspace = workspace
        self.task = task
        self.mode = mode
        self.injection = injection

    def call(self, tool_name: str, source: str = "agent", **kwargs: Any) -> Any:
        call = ToolCall(
            tool_name=tool_name,
            args=kwargs,
            source=source,
            risk_level="high" if is_write_tool(tool_name) else "low",
        )
        if self.mode == "secure_mode" and not is_tool_allowed(self.task, tool_name, self.mode):
            call.allowed = False
            call.reason = "bloqueado pelo tool filter"
            call.risk_level = "high"
            self.workspace.log_tool_call(call)
            return None

        call = guard_tool_call(self.task, call, self.mode, self.injection)
        self.workspace.log_tool_call(call)
        if not call.allowed:
            return None

        method = getattr(self.workspace, tool_name)
        return method(**kwargs)

