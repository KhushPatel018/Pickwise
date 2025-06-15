"""
Absolute Rating Computation node for the resume processor workflow.
Calculates final scores and makes decisions based on thresholds.
"""
from decimal import Decimal
import logging
from typing import Dict, Any, Tuple
from workflows.resume_processor.state import ResumeProcessorState
from workflows.resume_processor.consts import (
    DEFAULT_ABSOLUTE_RATING_WEIGHTS,
    DEFAULT_ABSOLUTE_RATING_THRESHOLD,
    DEFAULT_ABSOLUTE_RATING_ERROR_BOUNDARY
)
import json
from utils.config import load_config
from utils.dynamo_client import DynamoClient
load_config()

logger = logging.getLogger(__name__)

class AbsoluteRatingNode:
    def __init__(self):
        """Initialize Absolute Rating node."""
        pass

    def compute_rating(self, state: ResumeProcessorState) -> ResumeProcessorState:
        """
        Compute absolute rating and make final decision.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple[ResumeProcessorState, str]: Updated state and next node
        """
        try:
            dynamo_client = DynamoClient()
            # Get weights from state or use defaults
            weights = state.get('weights') or DEFAULT_ABSOLUTE_RATING_WEIGHTS

            logger.info(f"[scores from previous nodes] Cultural fit score: {state['cultural_fit_score']} Uniqueness score: {state['uniqueness_score']} JD score: {state['jd_score']} Custom criteria scores: {json.dumps(state['custom_criteria_scores'])}")
            
            # Get threshold and error boundary from state or use defaults
            threshold = state.get('absolute_grading_threshold') or DEFAULT_ABSOLUTE_RATING_THRESHOLD
            error_boundary = state.get('absolute_grading_error_boundary') or DEFAULT_ABSOLUTE_RATING_ERROR_BOUNDARY
            
            # Calculate weighted score
            absolute_score = self._calculate_weighted_score(state, weights)
            
            # Determine status based on thresholds
            status, message = self._determine_status(absolute_score, threshold, error_boundary)
            
            state['absolute_score'] = absolute_score
            state['status'] = status  # Set workflow status to match decision

            logger.info(f"[AbsoluteRatingNode] Absolute score: {absolute_score}")

            # update absolute score in dynamo db
            if dynamo_client.update_item(
                key={'candidate_id': state['candidate_id'], 'job_id': state['job_id']},
                update_expression=(
                    'SET #absolute_score = :absolute_score, #status = :status, #verdict_comment = :verdict_comment'
                ),
                expression_values={
                    ':absolute_score': Decimal(str(absolute_score)),
                    ':status': status,
                    ':verdict_comment': message
                },
                expression_attribute_names={
                    '#absolute_score': 'absolute_score',
                    '#status': 'status',
                    '#verdict_comment': 'verdict_comment'
                }
            ):
                logger.info(f"[AbsoluteRatingNode] Updated absolute score in dynamo db: {absolute_score}, status: {status}, verdict_comment: {message}")
            
            state['next_node'] = 'end'
            return state

        except Exception as e:
            # Only set FAILED status for actual errors
            logger.error(f"[AbsoluteRatingNode] Error in absolute rating computation: {str(e)}")
            state['status'] = 'FAILED'
            state['error_message'] = f'Absolute rating error: {str(e)}'
            state['next_node'] = 'end'
            return state

    def _calculate_weighted_score(self, state: ResumeProcessorState, weights: Dict[str, Any]) -> float:
        """
        Calculate weighted score from all components.
        Input scores are out of 10, weights are out of 10 (sum to 10).
        Final score will be out of 100.
        
        Args:
            state: Current workflow state
            weights: Weights for different scoring components
            
        Returns:
            float: Calculated absolute score (0-100)
        """
        # Calculate base weighted score (input scores are 0-10)

        base_score = (
            state['jd_score'] * weights['jd_score_weight'] +
            state['cultural_fit_score'] * weights['cultural_fit_score_weight'] +
            state['uniqueness_score'] * weights['uniqueness_score_weight']
        )
        
        # Calculate custom criteria score if present
        custom_score = 0.0
        if state.get('custom_criteria_scores'):
            custom_criteria_weights = weights.get('custom_criteria_score_weight', {})
            weighted_custom_scores = []
            
            for criteria_obj in state['custom_criteria_scores']:
                criteria_name = criteria_obj['name']
                if criteria_name in custom_criteria_weights:
                    weight = custom_criteria_weights[criteria_name]
                    weighted_custom_scores.append(criteria_obj['score'] * weight)
            
            if weighted_custom_scores:
                custom_score = sum(weighted_custom_scores)
        
        # Combine scores (weights sum to 10, so final score will be 0-100)
        return base_score + custom_score

    def _determine_status(self, score: float, threshold: float, error_boundary: float) -> Tuple[str, str]:
        """
        Determine final status based on score and thresholds.
        
        Args:
            score: Calculated absolute score
            threshold: Base threshold for decision making
            error_boundary: Error boundary for decision zones
            
        Returns:
            Tuple[str, str]: Status and message
        """
        lower_bound = threshold - error_boundary
        upper_bound = threshold + error_boundary
        
        if score < lower_bound:
            return 'REJECTED', f'Score {score:.2f} below threshold {lower_bound:.2f}'
        elif score > upper_bound:
            return 'SELECTED', f'Score {score:.2f} above threshold {upper_bound:.2f}'
        else:
            return 'IN_CONSIDERATION', f'Score {score:.2f} within consideration range'
