"""
Entrypoint for your LangGraph multi-agent app.
"""
from workflows.sample_workflow import build_workflow
from schemas.sample import SampleInput

if __name__ == "__main__":
    workflow = build_workflow()
    # Example: Run with dummy input
    result = workflow.run(SampleInput(text="Hello World"))
    print(result) 