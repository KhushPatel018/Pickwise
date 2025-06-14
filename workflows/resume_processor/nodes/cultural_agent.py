"""
Cultural Agent node for the resume processor workflow.
Analyzes cultural fit, uniqueness, and custom criteria using LLM.
"""
import logging
import json
from typing import Dict, Any, Tuple
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from utils.s3_client import S3Client
from utils.dynamo_client import DynamoClient
from ..state import ResumeProcessorState, update_state, add_tool_message
from prompts.cultural_agent_prompt import CULTURAL_AGENT_PROMPT
import os
from utils.config import load_config

load_config()

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
        self.prompt = CULTURAL_AGENT_PROMPT

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
                'core_values_json': json.dumps(state['core_values_data'], indent=2),
                'uniqueness_definition': json.dumps(state['uniqueness_data']),
                'custom_criteria': json.dumps(state['custom_criteria_data'], indent=2)
            }

            # Get LLM analysis
            chain = self.prompt | self.llm
            analysis_result = chain.invoke(prompt_input)

            # Parse and validate analysis result
            try:
                analysis_data = self._parse_analysis_result(analysis_result)

                # update the state with scores
                state['cultural_fit_score'] = analysis_data['cultural_fit_score']
                state['uniqueness_score'] = analysis_data['uniqueness_score']
                state['custom_criteria_scores'] = analysis_data['custom_criteria_scores']
            except Exception as e:
                logger.error(f"[Cultural Agent] Failed to parse cultural analysis result: {str(e)}")
                state['error_message'] = f"[Cultural Agent] Failed to parse cultural analysis result: {str(e)}"
                state['overall_status'] = 'FAILED'
                return state, 'end'

            # Save analysis to S3 & DynamoDB
            try:
                analysis_key = f"s3://{os.getenv('S3_BUCKET_NAME')}/{state['job_id']}/{state['candidate_id']}/cultural_analysis.json"
                if not self.s3_client.put_object(analysis_key, json.dumps(analysis_data, indent=2)):
                    logger.error(f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}")
                    state['error_message'] = f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}"
                    state['overall_status'] = 'FAILED'
                    return state, 'end'
            except Exception as e:
                logger.error(f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}")
                state['error_message'] = f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}"
                state['overall_status'] = 'FAILED'
                return state, 'end'

            # Update status in DynamoDB to track progress
            try:
                if not self.dynamo_client.update_item(
                    key={'candidate_id': state['candidate_id']},
                    # set analysis_url, score and their justification
                    update_expression='SET analysis_url = :url, cultural_fit_score = :cultural_fit_score, uniqueness_score = :uniqueness_score, custom_criteria_scores = :custom_criteria_scores, cultural_fit_justification = :cultural_fit_justification, uniqueness_justification = :uniqueness_justification',
                    expression_values={
                        ':url': analysis_key, 
                        ':cultural_fit_score': state['cultural_fit_score'], 
                        ':uniqueness_score': state['uniqueness_score'], 
                        ':custom_criteria_scores': state['custom_criteria_scores'], 
                        ':cultural_fit_justification': analysis_data['cultural_fit_justification'], 
                        ':uniqueness_justification': analysis_data['uniqueness_justification']
                    }
                    ):
                    logger.error("Failed to update analysis saved status in DynamoDB") 
                    return state, 'end'
            except Exception as e:
                logger.error(f"[Cultural Agent] Failed to update analysis saved status in DynamoDB: {str(e)}")
                state['error_message'] = f"[Cultural Agent] Failed to update analysis saved status in DynamoDB: {str(e)}"
                state['overall_status'] = 'FAILED'
                return state, 'end'

            return state, 'absolute_rating'

        except Exception as e:
            logger.error(f"Unexpected error in cultural analysis: {str(e)}")
            state['error_message'] = f"[Cultural Agent] Unexpected error: {str(e)}"
            state['overall_status'] = 'FAILED'
            return state, 'end' 

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
            
            if json_str.endswith('```'):
                json_str = json_str[:-3]  # Remove ``` markers
            
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