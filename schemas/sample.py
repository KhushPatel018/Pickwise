from pydantic import BaseModel

class SampleInput(BaseModel):
    text: str

class SampleOutput(BaseModel):
    response: str 