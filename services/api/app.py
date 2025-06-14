from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers.workflow_controller import router as workflow_router

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