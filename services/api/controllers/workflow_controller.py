from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..models.workflow_request import WorkflowRequest
from ..models.workflow_response import WorkflowResponse
from ...workflows.sample_workflow import build_workflow
from ...schemas.sample import SampleInput

router = APIRouter()

@router.post("/workflows/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    try:
        # Initialize workflow
        workflow = build_workflow()
        
        # Prepare input
        workflow_input = SampleInput(text=request.input_text)
        
        # Run workflow
        result = workflow.run(workflow_input)
        
        return WorkflowResponse(
            success=True,
            result=result.dict(),
            message="Workflow executed successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        ) 