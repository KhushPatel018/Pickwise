from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional
import uuid
from core.pipeline import ResumeEvaluationPipeline
import boto3
import json
from datetime import datetime

app = FastAPI(title="Resume Evaluation Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize S3 client
s3_client = boto3.client('s3')

# In-memory storage for job results (replace with proper database in production)
job_results: Dict[str, dict] = {}

class EvaluationRequest(BaseModel):
    resume_url: HttpUrl
    job_description_url: HttpUrl
    company_values_url: HttpUrl
    example_resume_insights_output_template_url: Optional[HttpUrl] = None
    past_successes_insight_document: Optional[HttpUrl] = None

class EvaluationResponse(BaseModel):
    job_id: str
    status: str

class JobStatus(BaseModel):
    status: str
    results: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_resume(request: EvaluationRequest, background_tasks: BackgroundTasks):
    """Submit a resume for evaluation."""
    try:
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        job_results[job_id] = {
            "status": "processing",
            "results": None,
            "error": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Process the resume in the background
        background_tasks.add_task(
            process_resume_evaluation,
            job_id,
            request.dict()
        )
        
        return EvaluationResponse(job_id=job_id, status="processing")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Get the status of a resume evaluation job."""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_results[job_id]

@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """Get the results of a completed resume evaluation job."""
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_results[job_id]
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed yet")
    
    return job_data["results"]

async def process_resume_evaluation(job_id: str, input_payload: Dict):
    """Process resume evaluation in the background."""
    try:
        # Initialize the pipeline
        pipeline = ResumeEvaluationPipeline()
        
        # Run the evaluation
        results = pipeline.evaluate_resume(input_payload)
        
        # Update job status
        job_results[job_id].update({
            "status": "completed",
            "results": results,
            "updated_at": datetime.utcnow()
        })
        
    except Exception as e:
        # Update job status with error
        job_results[job_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow()
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 