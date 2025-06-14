"""
Example LangGraph workflow combining multiple agents.
"""
from langgraph.graph import StateGraph
from agents.sample_agent import sample_agent
 
def build_workflow():
    graph = StateGraph()
    graph.add_node("SampleAgent", sample_agent)
    # Add more nodes and edges as you scale
    return graph 