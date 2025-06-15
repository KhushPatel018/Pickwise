"""
Test script for Cultural Agent.
Runs the agent with sample data and displays the output.
"""
import os
import sys
import json
import logging

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from langchain_openai import ChatOpenAI
from utils.s3_client import S3Client
from utils.dynamo_client import DynamoClient
from utils.config import load_config
from workflows.resume_processor.nodes.cultural_agent import CulturalAgent
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
            "jd_score_weight": 4.0,    
            "cultural_fit_score_weight": 2.0,  
            "uniqueness_score_weight": 3.0,    
            "custom_criteria_score_weight": {  
                "Past Success": 0.5,
                "Diversity Hiring": 0.5
            }
        },
        jd_threshold=6,
        absolute_grading_error_boundary=5.0,
        absolute_grading_threshold=65.0
    )

def main():
    """Main test function."""
    try:
        # Load environment variables
        load_config()
        
        # Create test request
        request = create_test_request()
        
        # Initialize clients
        s3_client = S3Client()
        dynamo_client = DynamoClient()
        
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
        
        # Create Cultural Agent
        agent = CulturalAgent(llm)
        
        # Run analysis
        logger.info("Starting Cultural Analysis...")
        updated_state = agent.analyze_cultural_fit(state)
        
        # Print results
        logger.info("\n=== Cultural Analysis Results ===")
        logger.info(f"Next Node: {updated_state['next_node']}")
        
        if updated_state.get('error_message'):
            logger.error(f"Error: {updated_state.get('error_message')}")
        
        # Print detailed analysis if available
        # if updated_state.get('cultural_analysis_url'):
        #     analysis_data = s3_client.get_object(os.getenv('S3_BUCKET_NAME'),updated_state['cultural_analysis_url'])
        #     if analysis_data:
        #         logger.info("\n=== Detailed Analysis ===")
        #         print(json.dumps(json.loads(analysis_data), indent=2))
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 