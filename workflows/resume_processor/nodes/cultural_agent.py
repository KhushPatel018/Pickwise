"""
Cultural Agent node for the resume processor workflow.
Analyzes cultural fit, uniqueness, and custom criteria using LLM.
"""
import logging
import json
from typing import Dict, Any, Tuple
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from utils.aws.s3_client import S3Client
from utils.aws.dynamo_client import DynamoClient
from ..state import ResumeProcessorState, update_state, add_tool_message
from prompts.cultural_agent_prompt import combined_prompt

logger = logging.getLogger(__name__)

class CulturalAgent:
    def __init__(
        self,
        s3_client: S3Client,
        dynamo_client: DynamoClient,
        model_name: str = "gpt-4",
        temperature: float = 0.7
    ):
        """
        Initialize Cultural Agent.
        
        Args:
            s3_client: S3 client instance
            dynamo_client: DynamoDB client instance
            model_name: LLM model name
            temperature: LLM temperature setting
        """
        self.s3_client = s3_client
        self.dynamo_client = dynamo_client
        self.llm = ChatOpenAI(model_name=model_name, temperature=temperature)
        self.prompt = combined_prompt

    def analyze_cultural_fit(self, state: ResumeProcessorState) -> Tuple[ResumeProcessorState, str]:
        """
        Analyze cultural fit, uniqueness, and custom criteria.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple[ResumeProcessorState, str]: Updated state and next node
        """
        try:
            # Prepare input for LLM
            prompt_input = {
                'resume_json': json.dumps(state['resume_data'], indent=2),
                'core_values_json': json.dumps(state['core_values'], indent=2),
                'uniqueness_definition': state['uniqueness_description'].get('description', ''),
                'custom_criteria': json.dumps(state['custom_criteria'], indent=2)
            }

            # Get LLM analysis
            chain = self.prompt | self.llm
            analysis_result = chain.invoke(prompt_input)

            # Parse and validate analysis result
            try:
                analysis_data = self._parse_analysis_result(analysis_result)
            except Exception as e:
                logger.error(f"Failed to parse cultural analysis result: {str(e)}")
                return self._handle_error(state, 'Failed to parse cultural analysis'), 'end'

            # Save analysis to S3
            analysis_key = f"analysis/{state['candidate_id']}/cultural_analysis.json"
            if not self.s3_client.put_object(analysis_key, json.dumps(analysis_data, indent=2)):
                logger.error("Failed to save cultural analysis to S3")
                return self._handle_error(state, 'Failed to save cultural analysis'), 'end'

            # Update state with analysis results
            updated_state = update_state(
                state,
                cultural_analysis=analysis_data,
                cultural_fit_score=analysis_data['cultural_fit_score'] / 10.0,  # Normalize to 0-1
                uniqueness_score=analysis_data['uniqueness_score'] / 10.0,  # Normalize to 0-1
                custom_criteria_scores={
                    item['name']: item['score'] / 10.0  # Normalize to 0-1
                    for item in analysis_data['custom_criteria_scores']
                }
            )

            # Update database
            self._update_db_status(
                state['candidate_id'],
                'CULTURAL_ANALYZED',
                'Cultural analysis completed'
            )

            return updated_state, 'absolute_rating'

        except Exception as e:
            logger.error(f"Unexpected error in cultural analysis: {str(e)}")
            return self._handle_error(state, str(e)), 'end'

    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """
        Parse LLM analysis result into structured format.
        
        Args:
            result: Raw LLM analysis result
            
        Returns:
            Dict[str, Any]: Structured analysis data
        """
        try:
            # Extract JSON from the response
            json_str = result.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:-3]  # Remove ```json and ``` markers
            elif json_str.startswith('```'):
                json_str = json_str[3:-3]  # Remove ``` markers
            
            analysis_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                'cultural_fit_score',
                'cultural_fit_justification',
                'core_value_scores',
                'uniqueness_score',
                'uniqueness_justification',
                'custom_criteria_scores'
            ]
            
            for field in required_fields:
                if field not in analysis_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error parsing analysis result: {str(e)}")
            raise

    def _handle_error(self, state: ResumeProcessorState, error_message: str) -> ResumeProcessorState:
        """
        Handle errors in cultural analysis.
        
        Args:
            state: Current state
            error_message: Error message
            
        Returns:
            ResumeProcessorState: Updated state with error
        """
        self._update_db_status(
            state['candidate_id'],
            'ERROR',
            f'Cultural analysis error: {error_message}'
        )
        return update_state(
            state,
            status='ERROR',
            error=error_message
        )

    def _update_db_status(self, candidate_id: str, status: str, message: str) -> None:
        """
        Update candidate status in database.
        
        Args:
            candidate_id: Candidate ID
            status: New status
            message: Status message
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