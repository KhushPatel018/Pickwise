"""
Example agent for LangGraph workflow.
"""
from prompts import load_prompt
from schemas.sample import SampleInput, SampleOutput
from utils.openai_client import ask_llm

def sample_agent(input: SampleInput) -> SampleOutput:
    prompt = load_prompt("sample_prompt.txt")
    response = ask_llm(prompt.format(user_input=input.text))
    return SampleOutput.parse_raw(response) 