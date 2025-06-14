from pydantic import BaseModel

class WorkflowRequest(BaseModel):
    input_text: str
    parameters: dict = {}  # Optional parameters for workflow customization 