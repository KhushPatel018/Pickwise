from utils.s3_client import S3Client
from workflows.resume_processor.state import ResumeProcessorState
from models.workflow_request import WorkflowRequest
import json
import logging

logger = logging.getLogger(__name__)

class WorkflowService:
    @staticmethod
    def build_state(request: WorkflowRequest) -> ResumeProcessorState:
        """ 
        Build the state for the workflow using the request information.
        
        Args:
            request: WorkflowRequest containing all necessary S3 URLs and configuration
            
        Returns:
            ResumeProcessorState: Initialized state with all required data
            
        Raises:
            Exception: If any required data cannot be fetched or parsed
        """
        try:
            # Initialize clients
            s3_client = S3Client()

            # Fetch all required JSON files from S3
            s3_urls = [
                request.resume_s3_url,
                request.jd_s3_url,
                request.core_values_s3_url, 
                request.uniqueness_description_s3_url,
                request.custom_criteria_s3_url
            ]

            # Get all objects in one batch request
            s3_objects = s3_client.batch_get_objects(s3_urls)
            
            # Parse each JSON file into a dict
            try:
                resume_data = json.loads(s3_objects[request.resume_s3_url]['Body'].read().decode('utf-8'))
                jd_data = json.loads(s3_objects[request.jd_s3_url]['Body'].read().decode('utf-8'))
                core_values_data = json.loads(s3_objects[request.core_values_s3_url]['Body'].read().decode('utf-8'))
                uniqueness_data = json.loads(s3_objects[request.uniqueness_description_s3_url]['Body'].read().decode('utf-8'))
                custom_criteria_data = json.loads(s3_objects[request.custom_criteria_s3_url]['Body'].read().decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data: {str(e)}")
                raise Exception(f"Invalid JSON data in S3 objects: {str(e)}")
            except KeyError as e:
                logger.error(f"Missing required S3 object: {str(e)}")
                raise Exception(f"Missing required data: {str(e)}")

            # Add all data to state
            return ResumeProcessorState({
                'messages': [],
                'job_id': request.job_id,
                'candidate_id': request.candidate_id,
                'resume_data': resume_data,
                'jd_data': jd_data,
                'core_values_data': core_values_data,
                'uniqueness_data': uniqueness_data,
                'custom_criteria_data': custom_criteria_data,
                'weights': request.weights,
                'jd_threshold': request.jd_threshold,
                'absolute_grading_error_boundary': request.absolute_grading_error_boundary,
                'absolute_grading_threshold': request.absolute_grading_threshold,
                'status': 'INITIALIZED',
                'error_message': None,
                'next_node': 'jd_analysis_agent'
            })

        except Exception as e:
            logger.error(f"Failed to build workflow state: {str(e)}")
            raise Exception(f"Failed to initialize workflow state: {str(e)}")