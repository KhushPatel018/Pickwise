from pydantic import BaseModel
from typing import Dict, Any

class WorkflowResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    message: str 