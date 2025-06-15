"""
Configuration utility for loading environment variables.
"""
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def load_config():
    """
    Load environment variables from .env file.
    Raises an error if required variables are missing.
    """
    # Load .env file
    load_dotenv()
    
    # Required environment variables
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'S3_BUCKET_NAME',
        'DYNAMODB_TABLE_NAME',
        'AWS_SESSION_TOKEN',
        'OPENAI_API_KEY',
    ]
    
    # Check for missing variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    # Set default values for optional variables
    if not os.getenv('AWS_REGION'):
        os.environ['AWS_REGION'] = 'us-east-1'
    
    if not os.getenv('LOG_LEVEL'):
        os.environ['LOG_LEVEL'] = 'INFO'
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Environment configuration loaded successfully") 