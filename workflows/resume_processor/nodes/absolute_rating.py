"""
Absolute Rating Computation node for the resume processor workflow.
Calculates final scores and makes decisions based on thresholds.
"""
import logging
from typing import Dict, Any, Tuple
from ..state import ResumeProcessorState, update_state
from ..consts import (
    DEFAULT_ABSOLUTE_RATING_WEIGHTS,
    DEFAULT_ABSOLUTE_RATING_THRESHOLD,
    DEFAULT_ABSOLUTE_RATING_ERROR_BOUNDARY
)
from utils.aws.dynamo_client import update_candidate_status

logger = logging.getLogger(__name__)

class AbsoluteRatingNode:
    def __init__(
        self,
        threshold: float = DEFAULT_ABSOLUTE_RATING_THRESHOLD,
        error_boundary: float = DEFAULT_ABSOLUTE_RATING_ERROR_BOUNDARY,
        weights: Dict[str, Any] = None
    ):
        """
        Initialize Absolute Rating node.
        
        Args:
            threshold: Base threshold for decision making (default: 70.0)
            error_boundary: Error boundary for decision zones (default: 10.0)
            weights: Weights for different scoring components (default: from consts)
        """
        self.threshold = threshold
        self.error_boundary = error_boundary
        self.weights = weights or DEFAULT_ABSOLUTE_RATING_WEIGHTS

    def compute_rating(self, state: ResumeProcessorState) -> Tuple[ResumeProcessorState, str]:
        """
        Compute absolute rating and make final decision.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple[ResumeProcessorState, str]: Updated state and next node
        """
        try:
            # Get weights from state or use defaults
            weights = state.get('weights') or DEFAULT_ABSOLUTE_RATING_WEIGHTS
            self.weights = weights
            
            # Get threshold and error boundary from state or use defaults
            self.threshold = state.get('absolute_grading_threshold') or DEFAULT_ABSOLUTE_RATING_THRESHOLD
            self.error_boundary = state.get('absolute_grading_error_boundary') or DEFAULT_ABSOLUTE_RATING_ERROR_BOUNDARY
            
            # Calculate weighted score
            absolute_score = self._calculate_weighted_score(state)
            
            # Determine status based on thresholds
            status, message = self._determine_status(absolute_score)
            
            # Update state with final results
            updated_state = update_state(
                state,
                scores={
                    'absolute_score': absolute_score,
                    'jd_score': state.get('scores', {}).get('jd_score', 0),
                    'cultural_fit_score': state.get('scores', {}).get('cultural_fit_score', 0),
                    'uniqueness_score': state.get('scores', {}).get('uniqueness_score', 0),
                    'custom_criteria_scores': state.get('scores', {}).get('custom_criteria_scores', {})
                },
                candidate_status=status,
                errors=None  # Clear any previous errors
            )
            
            # Save final results to database using utility function
            update_candidate_status(
                state.get('dynamo_client'),
                state['candidate_id'],
                status,
                message,
                absolute_score
            )
            
            return updated_state, 'end'

        except Exception as e:
            logger.error(f"Error in absolute rating computation: {str(e)}")
            return self._handle_error(state, str(e)), 'end'

    def _calculate_weighted_score(self, state: ResumeProcessorState) -> float:
        """
        Calculate weighted score from all components.
        Input scores are out of 10, weights are out of 10 (sum to 10).
        Final score will be out of 100.
        
        Args:
            state: Current workflow state
            
        Returns:
            float: Calculated absolute score (0-100)
        """
        # Calculate base weighted score (input scores are 0-10)
        base_score = (
            state['jd_score'] * self.weights['jd_score_weight'] +
            state['cultural_fit_score'] * self.weights['cultural_fit_score_weight'] +
            state['uniqueness_score'] * self.weights['uniqueness_score_weight']
        )
        
        # Calculate custom criteria score if present
        custom_score = 0.0
        if state.get('custom_criteria_scores'):
            custom_criteria_weights = self.weights.get('custom_criteria_score_weight', {})
            weighted_custom_scores = []
            
            for criteria, score in state['custom_criteria_scores'].items():
                if criteria in custom_criteria_weights:
                    weight = custom_criteria_weights[criteria]
                    weighted_custom_scores.append(score * weight)
            
            if weighted_custom_scores:
                custom_score = sum(weighted_custom_scores)
        
        # Combine scores (weights sum to 10, so final score will be 0-100)
        return base_score + custom_score

    def _determine_status(self, score: float) -> Tuple[str, str]:
        """
        Determine final status based on score and thresholds.
        
        Args:
            score: Calculated absolute score
            
        Returns:
            Tuple[str, str]: Status and message
        """
        lower_bound = self.threshold - self.error_boundary
        upper_bound = self.threshold + self.error_boundary
        
        if score < lower_bound:
            return 'REJECTED', f'Score {score:.2f} below threshold {lower_bound:.2f}'
        elif score > upper_bound:
            return 'SELECTED', f'Score {score:.2f} above threshold {upper_bound:.2f}'
        else:
            return 'IN_CONSIDERATION', f'Score {score:.2f} within consideration range'

    def _handle_error(self, state: ResumeProcessorState, error_message: str) -> ResumeProcessorState:
        """
        Handle errors in absolute rating computation.
        
        Args:
            state: Current state
            error_message: Error message
            
        Returns:
            ResumeProcessorState: Updated state with error
        """
        # Update database using utility function
        update_candidate_status(
            state.get('dynamo_client'),
            state['candidate_id'],
            'ERROR',
            f'Absolute rating error: {error_message}',
            0.0
        )
        
        return update_state(
            state,
            candidate_status='ERROR',
            errors=[error_message],
            scores={
                'absolute_score': 0.0,
                'jd_score': state.get('scores', {}).get('jd_score', 0),
                'cultural_fit_score': state.get('scores', {}).get('cultural_fit_score', 0),
                'uniqueness_score': state.get('scores', {}).get('uniqueness_score', 0),
                'custom_criteria_scores': state.get('scores', {}).get('custom_criteria_scores', {})
            }
        ) 