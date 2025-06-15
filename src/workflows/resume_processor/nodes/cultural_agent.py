"""
Cultural Agent node for the resume processor workflow.
Analyzes cultural fit, uniqueness, and custom criteria using LLM.
"""
import logging
import json
from typing import Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from ..state import ResumeProcessorState
from utils.config import load_config
from prompts.cultural_agent_prompt import CULTURAL_AGENT_PROMPT
from utils.s3_client import S3Client
from utils.dynamo_client import DynamoClient
from decimal import Decimal

load_config()

logger = logging.getLogger(__name__)

class CulturalAgent:
    def __init__(
        self,
        llm: ChatOpenAI
    ):
        """
        Initialize Cultural Agent.
        
        Args:
            s3_client: S3 client instance
            dynamo_client: DynamoDB client instance
            model_name: LLM model name
            temperature: LLM temperature setting
        """
        self.llm = llm
        self.prompt = CULTURAL_AGENT_PROMPT


    def analyze_cultural_fit(self, state: ResumeProcessorState) -> Tuple[ResumeProcessorState, str]:
        """
        Analyze cultural fit, uniqueness, and custom criteria.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple[ResumeProcessorState, str]: Updated state and next node
        """
        logger.info(f"[Cultural Agent] Starting Cultural Agent...")
        try:
            s3_client = S3Client()
            dynamo_client = DynamoClient()

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
            
            logger.info(f"[Cultural Agent] Cultural AGENT LLM OUTPUT: {analysis_result}")

            # Parse and validate analysis result
            try:
                analysis_data = self._parse_analysis_result(analysis_result)

                # update the state with scores
                state['cultural_fit_score'] = analysis_data['cultural_fit_score']
                state['uniqueness_score'] = analysis_data['uniqueness_score']
                state['custom_criteria_scores'] = analysis_data['custom_criteria_scores']

                logger.info(f"[Cultural Agent] Scores updated in state: cultural_fit_score: {state['cultural_fit_score']}, uniqueness_score: {state['uniqueness_score']}, custom_criteria_scores: {json.dumps(state['custom_criteria_scores'], indent=2)}")
                
            except Exception as e:
                logger.error(f"[Cultural Agent] Failed to parse cultural analysis result: {str(e)}")
                state['error_message'] = f"[Cultural Agent] Failed to parse cultural analysis result: {str(e)}"
                state['status'] = 'FAILED'
                state['next_node'] = 'end'
                return state

            # Save analysis to S3 & DynamoDB
            try:
                analysis_key = f"{state['job_id']}/{state['candidate_id']}/cultural_analysis.json"
                if not s3_client.put_object(analysis_key, json.dumps(analysis_data, indent=2)):
                    logger.error(f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}")
                    state['error_message'] = f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}"
                    state['status'] = 'FAILED'
                    state['next_node'] = 'end'
                    return state
                
                logger.info(f"Cultural analysis saved successfully to S3: {analysis_key}")
                state['cultural_analysis_url'] = analysis_key


            except Exception as e:
                logger.error(f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}")
                state['error_message'] = f"[Cultural Agent] Failed to save cultural analysis to S3: {analysis_key} with error: {str(e)}"
                state['status'] = 'FAILED'
                state['next_node'] = 'end'
                return state

            # Update status in DynamoDB to track progress
            try:
                if dynamo_client.update_item(
                        key={'candidate_id': state['candidate_id'], 'job_id': state['job_id']},
                        update_expression='SET analysis_url = :url, #cultural_fit_score = :cultural_fit_score, #uniqueness_score = :uniqueness_score, #custom_criteria_scores = :custom_criteria_scores, #cultural_fit_justification = :cultural_fit_justification, #uniqueness_justification = :uniqueness_justification',
                        expression_values={
                            ':url': analysis_key,
                            ':cultural_fit_score': Decimal(str(state['cultural_fit_score'])),   # Only if float/int!
                            ':uniqueness_score': Decimal(str(state['uniqueness_score'])),       # Only if float/int!
                            ':custom_criteria_scores': state['custom_criteria_scores'],         # Dict/list? Pass as is!
                            ':cultural_fit_justification': analysis_data['cultural_fit_justification'],
                            ':uniqueness_justification': analysis_data['uniqueness_justification']
                        },
                        expression_attribute_names={
                            '#cultural_fit_score': 'cultural_fit_score',
                            '#uniqueness_score': 'uniqueness_score',
                            '#custom_criteria_scores': 'custom_criteria_scores',
                            '#cultural_fit_justification': 'cultural_fit_justification',
                            '#uniqueness_justification': 'uniqueness_justification'
                        }
                ):
                    logger.info(f"[Cultural Agent] Cultural analysis saved successfully to DynamoDB: {state['candidate_id']},{state['job_id']} with scores: {state['cultural_fit_score']}, {state['uniqueness_score']}, {state['custom_criteria_scores']}")
            
            except Exception as e:
                logger.error(f"[Cultural Agent] Failed to update analysis saved status in DynamoDB: {str(e)}")
                state['error_message'] = f"[Cultural Agent] Failed to update analysis saved status in DynamoDB: {str(e)}"
                state['status'] = 'FAILED'
                state['next_node'] = 'end'
                return state
    
            state['next_node'] = 'absolute_rating'
            return state

        except Exception as e:
            logger.error(f"Unexpected error in cultural analysis: {str(e)}")
            state['error_message'] = f"[Cultural Agent] Unexpected error: {str(e)}"
            state['status'] = 'FAILED'
            state['next_node'] = 'end'
            return state 

    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """
        Parse LLM analysis result into structured format.
        
        Args:
            result: Raw LLM analysis result
            
        Returns:
            Dict[str, Any]: Structured analysis data
        """
        try:
            if hasattr(result, 'content'):
                result = result.content

            result_dict = json.loads(result)

            logger.info(f"Parsed Analysis data: {result_dict}")
            
            return result_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"[Cultural Agent] Failed to parse JSON from LLM response: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[Cultural Agent] Error parsing analysis result: {str(e)}")
            raise