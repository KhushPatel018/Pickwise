from pydantic import BaseModel
from typing import Dict, Any, Optional
class WorkflowResponse(BaseModel):
    status_code: int
    description: str
    error_message: Optional[str] = None
    data: Dict[str, Any]