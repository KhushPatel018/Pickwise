from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn
from controllers.workflow_controller import router as workflow_router
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LangGraph Multi-Agent API",
    description="API for managing LangGraph-based multi-agent workflows",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflow_router, prefix="/api/v1", tags=["workflows"])

if __name__ == "__main__":
    logger.info("Starting FastAPI application...")
    uvicorn.run(
        "main:app",  # Updated to use the correct module path
        host=os.getenv('HOST', 'localhost'),
        port=int(os.getenv('PORT', 8000)),
        reload=True  # Enable auto-reload during development
    ) 