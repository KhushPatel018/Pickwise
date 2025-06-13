from typing import Dict, List, TypedDict, Annotated, Optional
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import json
import boto3
from typing import Literal

class EvaluationState(TypedDict):
    """State for the resume evaluation pipeline."""
    resume_data: Dict
    job_description: Dict
    company_values: Dict
    current_node: str
    scores: Dict[str, float]
    justifications: Dict[str, str]
    verdict: Optional[str]
    boundary_case: bool
    screening_questions: List[str]

class ResumeEvaluationPipeline:
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(model=model_name)
        self.s3_client = boto3.client('s3')
        self.graph = self._build_graph()
        self.JD_SCORE_THRESHOLD = 5.0

    def _fetch_s3_file(self, url: str) -> Dict:
        """Fetch and parse JSON file from S3."""
        bucket = url.split('/')[2]
        key = '/'.join(url.split('/')[3:])
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))

    def _build_graph(self) -> Graph:
        """Build the LangGraph workflow for resume evaluation."""
        workflow = StateGraph(EvaluationState)

        # Add nodes for different evaluation agents
        workflow.add_node("jd_analysis", self._jd_analysis_agent)
        workflow.add_node("routing_decision", self._routing_decision_agent)
        workflow.add_node("cultural_fit", self._cultural_fit_agent)
        workflow.add_node("uniqueness", self._uniqueness_agent)
        workflow.add_node("absolute_rating", self._absolute_rating_agent)
        workflow.add_node("boundary_case", self._boundary_case_agent)
        workflow.add_node("relative_ranking", self._relative_ranking_agent)
        workflow.add_node("screening_questions", self._screening_questions_agent)

        # Define the edges
        workflow.add_edge("jd_analysis", "routing_decision")
        workflow.add_edge("routing_decision", "cultural_fit")
        workflow.add_edge("cultural_fit", "uniqueness")
        workflow.add_edge("uniqueness", "absolute_rating")
        workflow.add_edge("absolute_rating", "boundary_case")
        workflow.add_edge("boundary_case", "relative_ranking")
        workflow.add_edge("relative_ranking", "screening_questions")

        # Set the entry point
        workflow.set_entry_point("jd_analysis")

        # Set the exit point
        workflow.set_finish_point("screening_questions")

        return workflow.compile()

    def _jd_analysis_agent(self, state: EvaluationState) -> EvaluationState:
        """Analyze job description alignment."""
        messages = [
            HumanMessage(content=f"""Analyze the resume against the job description.
            Resume: {json.dumps(state['resume_data'])}
            Job Description: {json.dumps(state['job_description'])}
            
            Provide:
            1. JD alignment score (0-10)
            2. Detailed justification
            3. Skill match breakdown""")
        ]
        response = self.llm.invoke(messages)
        
        # Parse response and update state
        state['scores']['jd_alignment'] = float(response.content.split('Score:')[1].split('\n')[0].strip())
        state['justifications']['jd_alignment'] = response.content
        state['current_node'] = 'jd_analysis'
        return state

    def _routing_decision_agent(self, state: EvaluationState) -> EvaluationState:
        """Make routing decision based on JD score."""
        jd_score = state['scores']['jd_alignment']
        
        if jd_score < self.JD_SCORE_THRESHOLD:
            state['verdict'] = "REJECTED"
            state['justifications']['routing'] = f"JD alignment score {jd_score} below threshold {self.JD_SCORE_THRESHOLD}"
            return state
        
        state['current_node'] = 'routing_decision'
        return state

    def _cultural_fit_agent(self, state: EvaluationState) -> EvaluationState:
        """Evaluate cultural fit and company values alignment."""
        messages = [
            HumanMessage(content=f"""Evaluate cultural fit and company values alignment.
            Resume: {json.dumps(state['resume_data'])}
            Company Values: {json.dumps(state['company_values'])}
            
            Provide:
            1. Cultural fit score (0-10)
            2. Detailed justification
            3. Value alignment breakdown""")
        ]
        response = self.llm.invoke(messages)
        
        state['scores']['cultural_fit'] = float(response.content.split('Score:')[1].split('\n')[0].strip())
        state['justifications']['cultural_fit'] = response.content
        state['current_node'] = 'cultural_fit'
        return state

    def _uniqueness_agent(self, state: EvaluationState) -> EvaluationState:
        """Evaluate uniqueness and standout factors."""
        messages = [
            HumanMessage(content=f"""Evaluate uniqueness and standout factors.
            Resume: {json.dumps(state['resume_data'])}
            
            Provide:
            1. Uniqueness score (0-10)
            2. Detailed justification
            3. Standout factors""")
        ]
        response = self.llm.invoke(messages)
        
        state['scores']['uniqueness'] = float(response.content.split('Score:')[1].split('\n')[0].strip())
        state['justifications']['uniqueness'] = response.content
        state['current_node'] = 'uniqueness'
        return state

    def _absolute_rating_agent(self, state: EvaluationState) -> EvaluationState:
        """Compute absolute rating based on all scores."""
        weights = {
            'jd_alignment': 0.5,
            'cultural_fit': 0.3,
            'uniqueness': 0.2
        }
        
        final_score = sum(
            state['scores'][key] * weight 
            for key, weight in weights.items()
        )
        
        state['scores']['final'] = final_score
        state['current_node'] = 'absolute_rating'
        return state

    def _boundary_case_agent(self, state: EvaluationState) -> EvaluationState:
        """Detect boundary cases requiring human review."""
        final_score = state['scores']['final']
        state['boundary_case'] = 4.5 <= final_score <= 5.5
        state['current_node'] = 'boundary_case'
        return state

    def _relative_ranking_agent(self, state: EvaluationState) -> EvaluationState:
        """Compute relative ranking and categorization."""
        final_score = state['scores']['final']
        
        if final_score >= 8.0:
            category = "Top"
        elif final_score >= 6.5:
            category = "Go-After"
        elif final_score >= 5.0:
            category = "Consider"
        else:
            category = "Sink"
            
        state['scores']['category'] = category
        state['current_node'] = 'relative_ranking'
        return state

    def _screening_questions_agent(self, state: EvaluationState) -> EvaluationState:
        """Generate screening questions."""
        messages = [
            HumanMessage(content=f"""Generate 3-5 screening questions based on:
            Resume: {json.dumps(state['resume_data'])}
            Evaluation Results: {json.dumps(state['scores'])}
            
            Focus on areas needing clarification or verification.""")
        ]
        response = self.llm.invoke(messages)
        
        state['screening_questions'] = [
            q.strip() for q in response.content.split('\n') 
            if q.strip().startswith(('1.', '2.', '3.', '4.', '5.'))
        ]
        state['current_node'] = 'screening_questions'
        return state

    def evaluate_resume(self, input_payload: Dict) -> Dict:
        """Evaluate a resume using the multi-agent pipeline."""
        # Fetch required data from S3
        resume_data = self._fetch_s3_file(input_payload['resume_url'])
        job_description = self._fetch_s3_file(input_payload['job_description_url'])
        company_values = self._fetch_s3_file(input_payload['company_values_url'])
        
        # Initialize state
        initial_state = EvaluationState(
            resume_data=resume_data,
            job_description=job_description,
            company_values=company_values,
            current_node="",
            scores={},
            justifications={},
            verdict=None,
            boundary_case=False,
            screening_questions=[]
        )
        
        # Run the pipeline
        final_state = self.graph.invoke(initial_state)
        
        return {
            "scores": final_state["scores"],
            "verdict": final_state["verdict"],
            "boundary_case": final_state["boundary_case"],
            "screening_questions": final_state["screening_questions"],
            "justifications": final_state["justifications"]
        } 