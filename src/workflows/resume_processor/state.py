"""
State management for the resume processor workflow.
"""
import logging
from typing import Dict, Any, Optional, List, TypedDict, Annotated, Sequence
from utils.s3_client import S3Client
from utils.dynamo_client import DynamoClient
from langchain_core.messages import BaseMessage
from operator import add as add_messages

logger = logging.getLogger(__name__)

class ResumeProcessorState(TypedDict):
    """
    State definition for the resume processor workflow.
    
    Attributes:
        messages: Sequence of messages in the conversation
        resume_data: Parsed resume data from S3
        jd_data: Parsed job description data from S3
        company_values_data: Company core values data from S3
        uniqueness_data: Company uniqueness definition from S3
        custom_criteria_data: Custom evaluation criteria from S3
        weights: Scoring weights for different components
        jd_threshold: Minimum JD match score threshold
        absolute_grading_error_boundary: Error boundary for absolute grading
        absolute_grading_threshold: Minimum threshold for absolute grading
        scores: Dict containing all computed scores (jd_score, cultural_fit_score, etc)
        job_id: Unique identifier for the job posting
        candidate_id: Unique identifier for the candidate
        status: Current workflow processing status
        errors: List of error messages if any occur during processing
        next_node: Next node to process in workflow graph
    """
    # Input data
    messages: Annotated[Sequence[BaseMessage], add_messages]
    resume_data: Optional[Dict[str, Any]]
    jd_data: Optional[Dict[str, Any]]
    core_values_data: Optional[Dict[str, Any]]
    uniqueness_data: Optional[Dict[str, Any]]
    custom_criteria_data: Optional[Dict[str, Any]]
    weights: Optional[Dict[str, Any]]
    jd_threshold: Optional[float]
    absolute_grading_error_boundary: Optional[float]
    absolute_grading_threshold: Optional[float]
    # Output scores
    jd_score: Optional[float]
    cultural_fit_score: Optional[float]
    uniqueness_score: Optional[float]
    custom_criteria_scores: Optional[Dict[str, Any]]
    absolute_score: Optional[float]
    # Job and candidate IDs
    job_id: str
    candidate_id: str
    # Status and error handling
    status: str
    error_message: Optional[str]
    # Next node in workflow
    next_node: str
