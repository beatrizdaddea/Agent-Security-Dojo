from app.environment.workspace import Workspace
from app.schemas.tasks import InjectionTask


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

