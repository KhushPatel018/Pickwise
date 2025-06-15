"""
Router node for the resume processor workflow.
Makes decisions based on JD analysis score.
"""
import logging
from utils.dynamo_client import DynamoClient
from workflows.resume_processor.state import ResumeProcessorState
from utils.config import load_config
load_config()

logger = logging.getLogger(__name__)

class RouterNode:
    def __init__(self):
        """Initialize router node."""
        pass

    def route(self, state: ResumeProcessorState) -> ResumeProcessorState:
        """
        Route based on JD analysis score.
        
        Args:
            state (ResumeProcessorState): Current workflow state
            
        Returns:
            Tuple[ResumeProcessorState, str]: Updated state and next node
        """
        try:
            logger.info(f"[RouterNode] Routing based on JD score: {state['jd_score']}")
            jd_score = state['jd_score']
            jd_threshold = state['jd_threshold']

            if jd_score < jd_threshold:
                logger.info(f"JD score {jd_score} below threshold {jd_threshold}")
                self._update_db_status(
                    state['candidate_id'],
                    state['job_id'],
                    'JD_REJECTED',
                )
                state['next_node'] = 'end'
                return state
            
            logger.info(f"JD score {jd_score} above threshold {jd_threshold}")
            self._update_db_status(
                state['candidate_id'],
                state['job_id'],
                'JD_APPROVED',
            )
            state['next_node'] = 'cultural_agent'
            return state

        except Exception as e:
            logger.error(f"[RouterNode] Unexpected error in router: {str(e)}")
            state['status'] = 'FAILED'
            state['error_message'] = f'Unexpected error in router: {str(e)}'
            state['next_node'] = 'end'
            return state

    def _update_db_status(self, candidate_id: str, job_id: str, status: str) -> None:
        """
        Update candidate status in database.
        
        Args:
            candidate_id (str): Candidate ID
            status (str): New status
        """
        dynamo_client = DynamoClient()
        try:
            dynamo_client.update_item(
                key={'candidate_id': candidate_id, 'job_id': job_id },
                update_expression='SET #status = :status',
                expression_values={
                    ':status': status
                },
                expression_attribute_names={
                    '#status': 'status'
                }
            )

        except Exception as e:
            logger.error(f"Failed to update database status: {str(e)}") 