"""
Test script for the complete Resume Processor Workflow.
Tests the entire workflow from JD analysis to absolute rating.
"""
import os
import sys
import json
import logging

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from langchain_openai import ChatOpenAI
from utils.config import load_config
from workflows.resume_processor.workflow import ResumeProcessorWorkflow
from models.workflow_request import WorkflowRequest
from services.workflow_service import WorkflowService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_request() -> WorkflowRequest:
    """Create a test workflow request with sample data."""
    return WorkflowRequest(
        candidate_id="test-candidate-001",
        job_id="h2-2025-backend-lead-2235",
        resume_s3_url="h2-2025-backend-lead-2235/config/resume-data.json",
        jd_s3_url="h2-2025-backend-lead-2235/config/job-description.json",
        core_values_s3_url="h2-2025-backend-lead-2235/config/core-values.json",
        uniqueness_description_s3_url="h2-2025-backend-lead-2235/config/uniqueness-defination.json",
        custom_criteria_s3_url="h2-2025-backend-lead-2235/config/custom-criteria.json",
        weights={
            "jd_score_weight": 8,    
            "cultural_fit_score_weight": 2,  
            "uniqueness_score_weight": 1.2,    
            "custom_criteria_score_weight": {  
                "Past Success": 0.6,
                "Diversity Hiring": 0.4
            }
        },
        jd_threshold=6,
        absolute_grading_error_boundary=5.0,
        absolute_grading_threshold=60.0
    )

def main():
    """Main test function."""
    try:
        # Load environment variables
        load_config()
        
        # Create test request
        request = create_test_request()
        
        # Build state using WorkflowService
        logger.info("Building workflow state...")
        state = WorkflowService.build_state(request)
        
        # Initialize OpenAI client
        llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.4,
            top_p=0.9,
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Create workflow
        workflow = ResumeProcessorWorkflow()
        
        # Run workflow
        logger.info("Starting workflow...")
        final_state = workflow.process_resume(state)
        
        # Print results
        logger.info("\n=== Workflow Results ===")
        logger.info(f"Status: {final_state.get('status', 'UNKNOWN')}")
        
        if final_state.get('error_message'):
            logger.error(f"Error: {final_state.get('error_message')}")
        
        # Print scores
        logger.info("\nScores:")
        if final_state.get('jd_score'):
            logger.info(f"JD Score: {final_state['jd_score']}")
        if final_state.get('cultural_fit_score'):
            logger.info(f"Cultural Fit Score: {final_state['cultural_fit_score']}")
        if final_state.get('uniqueness_score'):
            logger.info(f"Uniqueness Score: {final_state['uniqueness_score']}")
        if final_state.get('custom_criteria_scores'):
            logger.info("Custom Criteria Scores:")

        
        # Print analysis URLs
        logger.info("\nAnalysis URLs:")
        if final_state.get('jd_analysis_url'):
            logger.info(f"JD Analysis: {final_state['jd_analysis_url']}")
        if final_state.get('cultural_analysis_url'):
            logger.info(f"Cultural Analysis: {final_state['cultural_analysis_url']}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 