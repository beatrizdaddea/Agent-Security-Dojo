from app.environment.workspace import Workspace
from app.schemas.tasks import InjectionTask
from app.schemas.tool_calls import ToolObservation


def inject_attack(workspace: Workspace, injection: InjectionTask) -> None:
    if injection.attack_vector == "email_body":
        workspace.state.inbox[-1].body += f"\n\n{injection.payload}"
        workspace.state.inbox[-1].is_untrusted = True
        return
    if injection.attack_vector == "calendar_description":
        workspace.state.calendar[-1].description += f"\n\n{injection.payload}"
        workspace.state.calendar[-1].is_untrusted = True
        return
    if injection.attack_vector == "document_content":
        for document in workspace.state.drive:
            if document.name == "relatorio.txt":
                document.content += f"\n\n{injection.payload}"
                document.is_untrusted = True
                return
    raise ValueError(f"Vetor desconhecido: {injection.attack_vector}")


def observed_fixture(
    injection: InjectionTask, observations: list[ToolObservation]
) -> bool:
    field = {
        "email_body": "body",
        "calendar_description": "description",
        "document_content": "content",
    }[injection.attack_vector]
    for observation in observations:
        if not observation.tainted:
            continue
        items = (
            observation.value
            if isinstance(observation.value, list)
            else [observation.value]
        )
        if any(
            item.is_untrusted and injection.payload in getattr(item, field, "")
            for item in items
        ):
            return True
    return False
