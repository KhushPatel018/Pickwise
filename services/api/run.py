#!/usr/bin/env python3
import uvicorn
from .app import app
import os
from utils.config import load_config

load_config()

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=os.getenv('HOST') or 'localhost',
        port=os.getenv('PORT') or 8000,
        reload=True  # Enable auto-reload during development
    ) 