from app.attacks.injection_tasks import INJECTION_TASKS
from app.schemas.tasks import InjectionTask


def get_injection_task(injection_id: str) -> InjectionTask:
    for injection in INJECTION_TASKS:
        if injection.id == injection_id:
            return injection
    raise KeyError(injection_id)

