# LangGraph Multi-Agent Workflow Scaffold

## Project Structure

```
.
├── agents/                 # Agent implementations
│   └── __init__.py
├── workflows/             # LangGraph workflow definitions
│   └── __init__.py
├── prompts/              # Prompt templates and loader
│   ├── __init__.py
│   ├── load_prompt.py
│   └── sample_prompt.txt
├── schemas/              # Pydantic data models
│   ├── __init__.py
│   └── sample.py
├── services/             # External services and API
│   ├── __init__.py
│   └── api/             # FastAPI MVC application
│       ├── app.py       # FastAPI app configuration
│       ├── run.py       # Server entry point
│       ├── controllers/ # API route handlers
│       ├── models/      # API data models
│       ├── services/    # Business logic
│       └── repositories/# Data access layer
├── utils/               # Utility functions
│   ├── __init__.py
│   └── logger.py
├── tests/              # Test suite
│   └── __init__.py
├── main.py            # CLI entry point
├── requirements.txt   # Project dependencies
└── README.md         # Project documentation
```

## Architecture

### Core Components
- **Agents**: Individual agent implementations for specific tasks
- **Workflows**: LangGraph workflow definitions combining multiple agents
- **Prompts**: Template management for agent interactions
- **Schemas**: Data validation and type safety with Pydantic

### API Layer (MVC Architecture)
- **Controllers**: Handle HTTP requests and responses
- **Models**: Define data structures and validation rules
- **Services**: Implement business logic
- **Repositories**: Handle data persistence and external services

### Utilities
- Logging configuration
- Environment management
- Common helper functions

## Development Rules

### Code Organization
1. **Agents**
   - One agent per file
   - Clear input/output interfaces
   - Document agent capabilities and requirements

2. **Workflows**
   - Define workflow graphs in separate files
   - Document node relationships and data flow
   - Include error handling and retry logic

3. **API Layer**
   - Follow RESTful principles
   - Use dependency injection
   - Implement proper error handling
   - Document all endpoints with OpenAPI

4. **Models**
   - Use Pydantic for validation
   - Keep models focused and single-purpose
   - Include field descriptions and examples

### Best Practices
1. **Type Safety**
   - Use type hints throughout
   - Validate all inputs/outputs
   - Document complex types

2. **Error Handling**
   - Use custom exceptions
   - Implement proper logging
   - Return meaningful error messages

3. **Testing**
   - Write unit tests for all components
   - Include integration tests for workflows
   - Test API endpoints

4. **Documentation**
   - Document all public interfaces
   - Include usage examples
   - Keep README up to date

## Quick Start

1. Install requirements:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the API server:
   ```bash
   python3 -m services.api.run
   ```

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Development

### Adding New Features
1. Create appropriate models in `schemas/`
2. Implement agent logic in `agents/`
3. Define workflow in `workflows/`
4. Add API endpoints in `services/api/controllers/`
5. Write tests in `tests/`

### Running Tests
```bash
python3 -m pytest tests/
```

### Code Style
- Follow PEP 8 guidelines
- Use black for formatting
- Run flake8 for linting

# Resume Evaluation Multi-Agent Service

A sophisticated resume evaluation system built using LangGraph and LangChain that employs multiple AI agents to analyze and evaluate resumes comprehensively.

## Features

- Multi-agent architecture for specialized resume analysis
- Structured evaluation pipeline with 8 specialized agents
- Comprehensive scoring system
- Asynchronous processing
- Detailed feedback generation
- API endpoints for resume submission and evaluation

## System Architecture

The system consists of 8 specialized agents in a LangGraph pipeline:

1. **JD Analysis Agent**: Evaluates resume against job description
2. **Routing Decision**: Makes initial screening decisions
3. **Cultural Fit Agent**: Evaluates company values alignment
4. **Uniqueness Agent**: Identifies standout factors
5. **Absolute Rating**: Computes weighted final score
6. **Boundary Case**: Detects cases needing human review
7. **Relative Ranking**: Categorizes candidates
8. **Screening Questions**: Generates targeted questions

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your credentials:
   ```
   OPENAI_API_KEY=your_api_key_here
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   ```

## API Endpoints

### POST `/evaluate`
Submit a resume for evaluation.

Request body:
```json
{
  "resume_url": "s3://bucket/resume.json",
  "job_description_url": "s3://bucket/jd.json",
  "company_values_url": "s3://bucket/values.json",
  "example_resume_insights_output_template_url": "s3://bucket/template.json",
  "past_successes_insight_document": "s3://bucket/successes.json"
}
```

Response:
```json
{
  "job_id": "uuid",
  "status": "processing"
}
```

### GET `/status/{job_id}`
Check evaluation status.

Response:
```json
{
  "status": "processing|completed|failed",
  "results": null,
  "error": null,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### GET `/results/{job_id}`
Get evaluation results.

Response:
```json
{
  "scores": {
    "jd_alignment": 8.5,
    "cultural_fit": 7.2,
    "uniqueness": 6.8,
    "final": 7.6,
    "category": "Top"
  },
  "verdict": "PASS",
  "boundary_case": false,
  "screening_questions": [
    "Question 1",
    "Question 2",
    "Question 3"
  ],
  "justifications": {
    "jd_alignment": "...",
    "cultural_fit": "...",
    "uniqueness": "..."
  }
}
```

## Running the Service

```bash
uvicorn main:app --reload
```

The service will be available at `http://localhost:8000`. Access the API documentation at `http://localhost:8000/docs`.

## Scoring System

The final score is computed using weighted components:
- Job Description Alignment: 50%
- Cultural Fit: 30%
- Uniqueness: 20%

Candidates are categorized as:
- Top (≥ 8.0)
- Go-After (≥ 6.5)
- Consider (≥ 5.0)
- Sink (< 5.0)

## License

MIT 