from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime

class AgentRequest(BaseModel):
    input: Any
    parameters: Optional[dict] = None

class AgentResponse(BaseModel):
    agent_name: str
    layer: int
    status: str
    input: Any
    output: Any
    timestamp: str
    execution_time: float

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
