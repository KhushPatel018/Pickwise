from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..models.workflow_request import WorkflowRequest
from ..models.workflow_response import WorkflowResponse
from workflows.resume_processor.workflow import ResumeProcessorWorkflow

router = APIRouter()

@router.post("/workflows/resume_processor/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    try:
        # log the request
        logger.info(f"Received workflow request: {request}")

        # build the state for workflow & initialize the workflow
        state = build_state(request)
        
        workflow = ResumeProcessorWorkflow()

        # run the workflow
        final_state = workflow.process_resume(state)

        # create the response from final state
        if final_state.get('overall_status') == 'FAILED':
            return WorkflowResponse(
                status_code=500,
                description="Workflow execution failed",
                error_message=final_state.get('error_message'),
                data=final_state.dict()
            )

        return WorkflowResponse(
            status_code=200,
            description="Workflow execution completed",
            data=final_state.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        ) 