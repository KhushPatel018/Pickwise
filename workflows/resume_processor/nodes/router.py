"""
Router node for the resume processor workflow.
Makes decisions based on JD analysis score.
"""
import logging
from typing import Dict, Any, Tuple
from utils.aws.dynamo_client import DynamoClient

logger = logging.getLogger(__name__)

class RouterNode:
    def __init__(self, dynamo_client: DynamoClient, score_threshold: float = 0.7):
        """
        Initialize router node.
        
        Args:
            dynamo_client (DynamoClient): DynamoDB client instance
            score_threshold (float): Minimum score threshold for continuing
        """
        self.dynamo_client = dynamo_client
        self.score_threshold = score_threshold

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
            
            if jd_score < self.score_threshold:
                logger.info(f"JD score {jd_score} below threshold {self.score_threshold}")
                self._update_db_status(
                    state['candidate_id'],
                    'REJECTED',
                    f'JD score {jd_score} below threshold {self.score_threshold}'
                )
                return state, 'end'
            
            logger.info(f"JD score {jd_score} above threshold {self.score_threshold}")
            self._update_db_status(
                state['candidate_id'],
                'APPROVED',
                f'JD score {jd_score} above threshold {self.score_threshold}'
            )
            return state, 'next_analysis'  # Continue to next analysis node

        except Exception as e:
            logger.error(f"Unexpected error in router: {str(e)}")
            self._update_db_status(
                state['candidate_id'],
                'ERROR',
                f'Unexpected error in router: {str(e)}'
            )
            return state, 'end'

    def _update_db_status(self, candidate_id: str, status: str, message: str) -> None:
        """
        Update candidate status in database.
        
        Args:
            candidate_id (str): Candidate ID
            status (str): New status
            message (str): Status message
        """
        try:
            self.dynamo_client.update_item(
                key={'candidate_id': candidate_id},
                update_expression='SET #status = :status, message = :message',
                expression_values={
                    ':status': status,
                    ':message': message
                }
            )
        except Exception as e:
            logger.error(f"Failed to update database status: {str(e)}") 