"""
JD Analysis Agent node for the resume processor workflow.
Analyzes resume against job description using LLM.
"""
import logging
from typing import Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from prompts.jd_agent_prompt import JD_AGENT_PROMPT
from prompts.constants import SCORING_RUBRIC, JD_OUTPUT_FORMAT
import json
from ..state import ResumeProcessorState

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

    def analyze_resume(self, state: ResumeProcessorState) -> Tuple[ResumeProcessorState, str]:
        """
        Analyze resume against job description.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple[Dict[str, Any], str]: Updated state and next node
        """
        try:
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

            # Parse analysis result
            try:
                analysis_data = self._parse_analysis_result(analysis_result)
                # update the state with scores
                state['jd_score'] = analysis_data['Normalized Score (out of 10)']

            except Exception as e:
                logger.error(f"Failed to parse analysis result: {str(e)}")
                state['error_message'] = f"[JD Analysis Agent] Failed to parse analysis result: {str(e)}"
                state['overall_status'] = 'FAILED'
                return state, 'end'
            
            

            # Save analysis to S3 & DynamoDB
            analysis_key = f"{state['job_id']}/{state['candidate_id']}/jd_analysis.json"
            try:
                # Save detailed analysis to S3
                if not state.get('s3_client').put_object(
                    analysis_key, 
                    json.dumps(analysis_data, indent=2)
                ):
                    logger.error(f"[JD Analysis Agent] Failed to save analysis to S3: {analysis_key} with error: {str(e)}")
                    state['error_message'] = f"[JD Analysis Agent] Failed to save analysis to S3: {analysis_key} with error: {str(e)}"
                    state['overall_status'] = 'FAILED'
                    return state, 'end'
                
                state['jd_analysis_url'] = analysis_key
                verdict = "APPROVED" if analysis_data['Verdict'] == True else "REJECTED"

                # Update status in DynamoDB to track progress
                if not state.get('dynamo_client').update_item(
                    key={'candidate_id': state['candidate_id']},
                    update_expression='SET jd_analysis_score = :score, jd_analysis_url = :url, jd_analysis_verdict = :verdict',
                    expression_values={
                        ':score': state['jd_score'], ':url': analysis_key, ':verdict': verdict
                    }
                ):
                    logger.error(f"[JD Analysis Agent] Failed to update analysis saved status in DynamoDB: {str(e)}") 
                    state['error_message'] = f"[JD Analysis Agent] Failed to update analysis saved status in DynamoDB: {str(e)}"
                    state['overall_status'] = 'FAILED'
                    return state, 'end'

            except Exception as e:
                logger.error(f"Error saving analysis: {str(e)}")
                state['error_message'] = f"[JD Analysis Agent] Failed to save analysis: {str(e)}"
                state['overall_status'] = 'FAILED'
                return state, 'end'
            
            return state, 'router'

        except Exception as e:
            logger.error(f"Unexpected error in JD analysis: {str(e)}")
            state['error_message'] = f"[JD Analysis Agent] Unexpected error: {str(e)}"
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
                'Raw Score (out of 100)',
                'Normalized Score (out of 10)',
                'Score Breakdown',
                'Detailed Scoring',
                'Key Strengths',
                'Areas for Improvement',
                'Verdict'
            ]
            
            for field in required_fields:
                if field not in analysis_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return analysis_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
            return {
                "status": "FAILED",
                "message": f"Failed to parse JSON from LLM response: {str(e)}",
                "scores": {}
            }
        except Exception as e:
            logger.error(f"Error parsing analysis result: {str(e)}")
            return {
                "status": "FAILED",
                "message": f"Error parsing analysis result: {str(e)}",
                "scores": {}
            } 