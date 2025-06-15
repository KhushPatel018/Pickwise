"""
Main workflow file for resume processing.
Connects all nodes and defines the workflow graph.
"""
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .nodes.jd_analysis_agent import JDAnalysisAgent
from .nodes.router import RouterNode
from .nodes.cultural_agent import CulturalAgent
from .nodes.absolute_rating import AbsoluteRatingNode
from .state import ResumeProcessorState
from langchain_openai import ChatOpenAI
import os
from utils.config import load_config

logger = logging.getLogger(__name__)
load_config()

class ResumeProcessorWorkflow:
    def __init__(
        self
    ):
        """
        Initialize resume processor workflow.
        
        Args:
            score_threshold: Minimum score threshold for continuing
            error_boundary: Error boundary for decision zones
            weights: Weights for different scoring components
        """
        # Initialize nodes
        self.llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, top_p=0.9, api_key=os.getenv('OPENAI_API_KEY'))
        self.jd_analysis = JDAnalysisAgent(self.llm)
        self.router = RouterNode()
        self.cultural_agent = CulturalAgent(self.llm)
        self.absolute_rating = AbsoluteRatingNode()

        # Create and compile workflow graph
        self.workflow = self._create_workflow()
        self.compiled_workflow = self.workflow.compile()

    def _create_workflow(self) -> StateGraph:
        """
        Create the workflow graph.
        
        Returns:
            StateGraph: Configured workflow graph
        """
        # Create graph
        workflow = StateGraph(ResumeProcessorState)

        # Add nodes
        workflow.add_node("jd_analysis", self.jd_analysis.analyze_resume)
        workflow.add_node("router", self.router.route)
        workflow.add_node("cultural_agent", self.cultural_agent.analyze_cultural_fit)
        workflow.add_node("absolute_rating", self.absolute_rating.compute_rating)

        # Add conditional edges
        workflow.add_conditional_edges(
            "jd_analysis",
            self._should_end,
            {
                True: END,
                False: "router"
            }
        )

        workflow.add_conditional_edges(
            "router",
            self._should_end,
            {
                True: END,
                False: "cultural_agent"
            }
        )

        workflow.add_conditional_edges(
            "cultural_agent",
            self._should_end,
            {
                True: END,
                False: "absolute_rating"
            }
        )

        # Set entry point
        workflow.set_entry_point("jd_analysis")

        return workflow

    def process_resume(self, state: ResumeProcessorState) -> ResumeProcessorState:
        """
        Process a resume through the workflow.
        
        Args:
            state: Initial workflow state with all required data
            
        Returns:
            ResumeProcessorState: Final workflow state
        """
        try:
            logger.info(f"Starting resume processing for candidate {state['candidate_id']}")
            
            # Run workflow
            final_state = self.compiled_workflow.invoke(state)
            
            logger.info(f"Completed resume processing for candidate {state['candidate_id']}")
            final_state['status'] = 'COMPLETED'
            return final_state

        except Exception as e:
            logger.error(f"Error in resume processing workflow: {str(e)}")
            raise
    
    def _should_end(self, state: ResumeProcessorState) -> bool:
        """
        Check if JD analysis should end.
        """
        return state['next_node'] == 'end'