import os

def load_prompt(prompt_name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), prompt_name)
    with open(path, 'r') as f:
        return f.read() 