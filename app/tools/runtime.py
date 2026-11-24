from typing import Any

from pydantic import ValidationError

from app.defenses.tool_call_guard import guard_tool_call
from app.defenses.tool_filter import ALL_TOOLS, WRITE_TOOLS
from app.environment.workspace import Workspace
from app.schemas.tasks import UserTask
from app.schemas.tool_calls import ToolCall, ToolObservation, ToolRequest


class ToolRuntime:
    def __init__(self, workspace: Workspace, task: UserTask, mode: str):
        self.workspace = workspace
        self.task = task.model_copy(deep=True)
        self.mode = mode
        self.taint_sources: tuple[str, ...] = ()
        self._write_completed = False
        self._pending: tuple[str, ToolCall] | None = None

    def authorize(self, request: ToolRequest, *, source: str = "agent") -> None:
        if self._pending is not None:
            raise RuntimeError("A tool request is already pending")

        call = ToolCall(
            tool_name=request.name,
            source=source,
            taint_sources=self.taint_sources,
            risk_level="high" if request.name in WRITE_TOOLS else "low",
        )
        schema = ALL_TOOLS.get(request.name)
        if schema is None:
            call.allowed = False
            call.reason = "UNKNOWN_TOOL"
        else:
            try:
                if isinstance(request.arguments, str):
                    arguments = schema.model_validate_json(request.arguments)
                else:
                    arguments = schema.model_validate(request.arguments)
                call.args = arguments.model_dump()
            except ValidationError:
                call.allowed = False
                call.reason = "INVALID_ARGUMENTS"
            if call.allowed:
                call = guard_tool_call(
                    self.task,
                    call,
                    self.mode,
                    canaries=self.workspace.state.canaries,
                    write_completed=self._write_completed,
                )
        self._pending = (request.id, call)

    def execute(self) -> ToolObservation:
        if self._pending is None:
            raise RuntimeError("No authorized tool request is pending")
        request_id, call = self._pending
        self._pending = None
        self.workspace.log_tool_call(call)
        observation = ToolObservation(request_id=request_id, call=call)
        if not call.allowed:
            observation.error = call.reason
            return observation

        try:
            if self.mode == "secure_mode" and call.tool_name == "search_drive":
                value = self.workspace.search_drive(
                    **call.args, allowed_names=self.task.authorized_documents
                )
            else:
                method = getattr(self.workspace, call.tool_name)
                value = method(**call.args)
        except KeyError:
            call.reason = observation.error = "RESOURCE_NOT_FOUND"
            return observation

        call.executed = True
        if call.tool_name in WRITE_TOOLS:
            self._write_completed = True
        observation.value = value
        items = value if isinstance(value, list) else [value]
        observation.tainted = any(
            getattr(item, "is_untrusted", False) for item in items
        )
        if observation.tainted:
            self.taint_sources += (request_id,)
        return observation

    def call(self, tool_name: str, source: str = "agent", **kwargs: Any) -> Any:
        request = ToolRequest(
            id=f"runtime-{len(self.workspace.state.tool_logs) + 1}",
            name=tool_name,
            arguments=kwargs,
        )
        self.authorize(request, source=source)
        return self.execute().value
