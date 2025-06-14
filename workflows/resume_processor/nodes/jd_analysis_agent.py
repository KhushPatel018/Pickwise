"""
JD Analysis Agent node for the resume processor workflow.
Analyzes resume against job description using LLM.
"""
import logging
from typing import Dict, Any, Tuple
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from prompts.jd_agent_prompt import JD_AGENT_PROMPT
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
        self.prompt = PromptTemplate.from_template(JD_AGENT_PROMPT)

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
                'job_description': state['jd_data']
            }

            # Get LLM analysis
            chain = self.prompt | self.llm
            analysis_result = chain.invoke(prompt_input)

            # Parse analysis result
            try:
                analysis_data = self._parse_analysis_result(analysis_result)
            except Exception as e:
                logger.error(f"Failed to parse analysis result: {str(e)}")
                update_candidate_status(
                    state.get('dynamo_client'),
                    state['candidate_id'],
                    'ERROR',
                    'Failed to parse analysis'
                )
                return state, 'end'

            # Save analysis using utility function
            analysis_key = f"analysis/{state['candidate_id']}/jd_analysis.json"
            try:
                # Save detailed analysis to S3
                if not state.get('s3_client').put_object(
                    analysis_key, 
                    json.dumps(analysis_data, indent=2)
                ):
                    logger.error("Failed to save analysis to S3")
                    update_candidate_status(
                        state.get('dynamo_client'),
                        state['candidate_id'],
                        'ERROR',
                        'Failed to save analysis to S3'
                    )
                    return state, 'end'

                # Update status in DynamoDB to track progress
                if not state.get('dynamo_client').update_item(
                    key={'candidate_id': state['candidate_id']},
                    update_expression='SET analysis_saved = :saved',
                    expression_values={':saved': True}
                ):
                    logger.error("Failed to update analysis saved status in DynamoDB") 
                    return state, 'end'

            except Exception as e:
                logger.error(f"Error saving analysis: {str(e)}")
                update_candidate_status(
                    state.get('dynamo_client'),
                    state['candidate_id'],
                    'ERROR',
                    f'Failed to save analysis: {str(e)}'
                )
                return state, 'end'

            # Update state with analysis results
            state['analysis_data'] = analysis_data
            state['jd_score'] = analysis_data['overall_score']
            
            # Update status using utility function
            update_candidate_status(
                state.get('dynamo_client'),
                state['candidate_id'],
                'ANALYZED',
                'JD analysis completed'
            )

            return state, 'router'

        except Exception as e:
            logger.error(f"Unexpected error in JD analysis: {str(e)}")
            update_candidate_status(
                state.get('dynamo_client'),
                state['candidate_id'],
                'ERROR',
                f'Unexpected error: {str(e)}'
            )
            return state, 'end'

    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """
        Parse LLM analysis result into structured format.
        
        Args:
            result: Raw LLM analysis result
            
        Returns:
            Dict[str, Any]: Structured analysis data
        """
        # Implementation depends on the expected output format
        # This is a placeholder - implement according to your needs
        # TODO: Implement this
        return {
            'overall_score': 0.0,  # Calculate from result
            'skill_matches': [],   # Extract from result
            'experience_matches': [],  # Extract from result
            'education_matches': [],   # Extract from result
            'analysis_summary': ''     # Extract from result
        } 