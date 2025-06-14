"""
State management for the resume processor workflow.
Defines the state structure and helper methods.
"""
from typing import TypedDict, Annotated, Sequence, Dict, Any, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from operator import add as add_messages
import logging
from utils.aws.s3_client import S3Client
from utils.aws.dynamo_client import DynamoClient
logger = logging.getLogger(__name__)

class ResumeProcessorState(TypedDict):
    """
    State definition for the resume processor workflow.
    
    Attributes:
        messages: Sequence of messages in the conversation
        resume_data: Parsed resume data
        jd_data: Parsed job description data
        analysis_data: Results from JD analysis
        jd_score: Overall JD match score
        candidate_id: Unique identifier for the candidate
        status: Current processing status
        error: Any error message if processing failed
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    resume_data: Optional[Dict[str, Any]]
    jd_data: Optional[Dict[str, Any]]
    company_values_data: Optional[Dict[str, Any]]
    uniqueness_data: Optional[Dict[str, Any]]
    custom_criteria_data: Optional[Dict[str, Any]]
    weights: Optional[Dict[str, Any]]
    jd_threshold: Optional[float]
    absolute_grading_error_boundary: Optional[float]
    absolute_grading_threshold: Optional[float]
    scores: Optional[Dict[str, Any]]
    job_id: str
    candidate_id: str
    candidate_status: str
    s3_client: S3Client
    dynamo_client: DynamoClient
    errors: Optional[List[str]]
