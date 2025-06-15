from fastapi import APIRouter, HTTPException
from models.workflow_request import WorkflowRequest
from models.workflow_response import WorkflowResponse
from workflows.resume_processor.workflow import ResumeProcessorWorkflow
from services.workflow_service import WorkflowService
from utils.logger import get_logger

router = APIRouter()

logger = get_logger(__name__)

@router.post("/workflows/resume_processor/run", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest) -> WorkflowResponse:
    try:
        # log the request
        logger.info(f"Received workflow request: {request}")

        # build the state for workflow & initialize the workflow
        state = WorkflowService.build_state(request)

        workflow = ResumeProcessorWorkflow()

        # run the workflow
        final_state = workflow.process_resume(state)

        # Handle error cases
        if final_state.get('status') == 'FAILED' or final_state.get('error_message'):
            logger.error(f"Workflow failed: {final_state.get('error_message')}")
            return WorkflowResponse(
                status_code=500,
                description="Workflow execution failed",
                error_message=final_state.get('error_message'),
                data=final_state
            )
        
        # Handle rejection case (this is a valid business case, not an error)
        if final_state.get('status') == 'REJECTED':
            logger.info(f"Candidate rejected with score {final_state.get('absolute_score')}")
            return WorkflowResponse(
                status_code=200,
                description="Candidate rejected - score below threshold",
                data=final_state
            )

        # Success case
        logger.info("Workflow completed successfully")
        return WorkflowResponse(
            status_code=200,
            description="Workflow execution completed successfully",
            data=final_state
        )
        
    except Exception as e:
        logger.error(f"Workflow execution failed with exception: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        ) 