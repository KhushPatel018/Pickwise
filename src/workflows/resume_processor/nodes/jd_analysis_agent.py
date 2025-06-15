"""
JD Analysis Agent node for the resume processor workflow.
Analyzes resume against job description using LLM.
"""
import json
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from prompts.jd_agent_prompt import JD_AGENT_PROMPT
from prompts.constants import SCORING_RUBRIC, JD_OUTPUT_FORMAT
from workflows.resume_processor.state import ResumeProcessorState
from utils.s3_client import S3Client
from utils.dynamo_client import DynamoClient
from decimal import Decimal

logger = logging.getLogger(__name__)

class JDAnalysisAgent:
    def __init__(self, llm: ChatOpenAI):
        """
        Initialize JD Analysis Agent.
        
        Args:
            llm: Configured LLM instance
        """
        self.llm = llm
        self.prompt = JD_AGENT_PROMPT

    def analyze_resume(self, state: ResumeProcessorState) -> ResumeProcessorState:
        """
        Analyze resume against job description.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple[Dict[str, Any], str]: Updated state and next node
        """
        logger.info(f"[JD Analysis Agent] Starting JD Analysis Agent...")
        try:
            s3_client = S3Client()
            dynamo_client = DynamoClient()
            # Prepare input for LLM
            prompt_input = {
                'resume': state['resume_data'],
                'job_description': state['jd_data'],
                'scoring_rubric': json.dumps(SCORING_RUBRIC, indent=2),
                'output_format': json.dumps(JD_OUTPUT_FORMAT, indent=2)
            }

            # Get LLM analysis using instance prompt template
            chain = self.prompt | self.llm
            analysis_result = chain.invoke(prompt_input)

            logger.info(f"[JD Analysis Agent] JD AGENT LLM OUTPUT: {analysis_result}")

            # Parse analysis result
            try:
                analysis_data = self._parse_analysis_result(analysis_result)
                # update the state with scores
                state['jd_score'] = analysis_data['Normalized Score (out of 10)']
                logger.info(f"[JD Analysis Agent] Scores updated in state: jd_score: {state['jd_score']}")

            except Exception as e:
                logger.error(f"Failed to parse analysis result: {str(e)}")
                state['error_message'] = f"[JD Analysis Agent] Failed to parse analysis result: {str(e)}"
                state['status'] = 'FAILED'
                state['next_node'] = 'end'
                return state
            
            # Save analysis to S3 & DynamoDB
            try:
                # Save detailed analysis to S3
                analysis_key = f"{state['job_id']}/{state['candidate_id']}/jd_analysis.json"
                s3_client.put_object(
                    analysis_key, 
                    json.dumps(analysis_data, indent=2)
                )
                
                logger.info(f"[JD Analysis Agent] JD analysis saved successfully to S3: {analysis_key}")
                state['jd_analysis_url'] = analysis_key

                # Update status in DynamoDB to track progress
                verdict = "JD_APPROVED" if analysis_data['Verdict'] == True else "JD_REJECTED"

                dynamo_client.update_item(
                    key={'candidate_id': state['candidate_id'], 'job_id': state['job_id']},
                    update_expression='SET jd_score = :score, jd_analysis_url = :url, #status = :status',
                    expression_values={
                        ':score': Decimal(str(state['jd_score'])),
                        ':url': analysis_key,
                        ':status': "JD_APPROVED" if analysis_data['Verdict'] else "JD_REJECTED"
                    },
                    expression_attribute_names={
                        '#status': 'status'
                    }
                )

                logger.info(f"[JD Analysis Agent] JD analysis saved successfully to DynamoDB: {state['candidate_id']},{state['job_id']} with verdict: {verdict}")

            except Exception as e:
                logger.error(f"Error saving analysis to dynamo db or s3: {str(e)}")
                state['error_message'] = f"[JD Analysis Agent] Failed to save analysis to dynamo db or s3: {str(e)}"
                state['status'] = 'FAILED'
                state['next_node'] = 'end'
                return state
            
            state['next_node'] = 'router'
            return state

        except Exception as e:
            logger.error(f"Unexpected error in JD analysis by LLM: {str(e)}")
            state['error_message'] = f"[JD Analysis Agent] Unexpected error in JD analysis by LLM: {str(e)}"
            state['status'] = 'FAILED'
            state['next_node'] = 'end'
            return state

    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """
        Parse the analysis result from the LLM into a structured format.
        
        Args:
            result: Raw result from LLM
            
        Returns:
            Dict containing status, message, and scores
        """
        try:
            # Extract content from AIMessage
            if hasattr(result, 'content'):
                result = result.content

            # Parse JSON string
            result_dict = json.loads(result)
            
            return result_dict
        except Exception as e:
            logger.error(f"[JD Analysis Agent - _parse_analysis_result] Failed to parse analysis result: {str(e)}")