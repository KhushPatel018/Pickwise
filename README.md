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