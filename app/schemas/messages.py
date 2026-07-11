from pydantic import BaseModel


class AgentMessage(BaseModel):
    role: str
    content: str
    source: str = "agent"

