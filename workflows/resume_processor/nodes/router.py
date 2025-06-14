"""
Router node for the resume processor workflow.
Makes decisions based on JD analysis score.
"""
import logging
from typing import Dict, Any, Tuple
from utils.dynamo_client import DynamoClient

logger = logging.getLogger(__name__)

class RouterNode:
    def __init__(self):
        """Initialize router node."""
        pass

    def route(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Route based on JD analysis score.
        
        Args:
            state (Dict[str, Any]): Current workflow state
            
        Returns:
            Tuple[Dict[str, Any], str]: Updated state and next node
        """
        try:
            jd_score = state.get('jd_score', 0.0)
            jd_threshold = state.get('jd_threshold', 0.7)
            
            if jd_score < jd_threshold:
                logger.info(f"JD score {jd_score} below threshold {jd_threshold}")
                self._update_db_status(
                    state['candidate_id'],
                    'REJECTED',
                )
                return state, 'end'
            
            logger.info(f"JD score {jd_score} above threshold {jd_threshold}")
            self._update_db_status(
                state['candidate_id'],
                'APPROVED',
            )
            return state, 'cultural_agent'

        except Exception as e:
            logger.error(f"[RouterNode] Unexpected error in router: {str(e)}")
            state['status'] = 'FAILED'
            state['error_message'] = f'Unexpected error in router: {str(e)}'
            return state, 'end'

    def _update_db_status(self, candidate_id: str, status: str) -> None:
        """
        Update candidate status in database.
        
        Args:
            candidate_id (str): Candidate ID
            status (str): New status
        """
        try:
            self.dynamo_client.update_item(
                key={'candidate_id': candidate_id},
                update_expression='SET #status = :status',
                expression_values={
                    ':status': status
                }
            )
        except Exception as e:
            logger.error(f"Failed to update database status: {str(e)}") 