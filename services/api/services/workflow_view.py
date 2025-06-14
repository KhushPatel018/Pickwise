from typing import Dict, Any
from ..models.workflow_response import WorkflowResponse

class WorkflowView:
    @staticmethod
    def format_success_response(result: Dict[str, Any], message: str = "Workflow executed successfully") -> WorkflowResponse:
        return WorkflowResponse(
            success=True,
            result=result,
            message=message
        )
    
    @staticmethod
    def format_error_response(error_message: str) -> WorkflowResponse:
        return WorkflowResponse(
            success=False,
            result={},
            message=error_message
        ) 