"""
S3 client for AWS operations.
"""
import boto3
import os
import json
import logging
from typing import Dict, Any, Optional, List
from utils.config import load_config

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        """Initialize S3 client with AWS credentials from environment variables."""
        # Load environment configuration
        load_config()
        
        # Get AWS credentials from environment variables
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')

        # Configure AWS session
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            aws_session_token=aws_session_token,
            region_name=aws_region
        )

        # Initialize S3 client
        self.s3 = session.client('s3')
        logger.info("S3 client initialized successfully")

    def batch_get_objects(self, keys: List[str]) -> Dict[str, Any]:
        """
        Fetch multiple objects from S3 in a single request.
        
        Args:
            keys: List of S3 keys to fetch
            
        Returns:
            Dict mapping URLs to their contents
        """
        try:
            results = {}
            for key in keys:
                response = self.s3.get_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=key)
                results[key] = response
            return results
        except Exception as e:
            logger.error(f"Failed to batch get objects: {str(e)}")
            raise

    def save_analysis(self, key: str, analysis_data: Dict[str, Any]) -> bool:
        """
        Save analysis results to S3.
        
        Args:
            key: S3 key to save to
            analysis_data: Analysis data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3.put_object(
                Bucket=os.getenv('S3_BUCKET_NAME'),
                Key=key,
                Body=json.dumps(analysis_data, indent=2),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save analysis: {str(e)}")
            return False

    def get_object(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a single object from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            
        Returns:
            Dict containing object data or None if not found
        """
        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to get object {key} from bucket {bucket}: {str(e)}")
            return None

    def put_object(self, key: str, data: str) -> bool:
        """
        Put an object in S3.
        
        Args:
            key: S3 key to save to
            data: Data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3.put_object(
                Bucket=os.getenv('S3_BUCKET_NAME'),
                Key=key,
                Body=data,
                ContentType='application/json'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to put object {key}: {str(e)}")
            return False

    def delete_object(self, key: str) -> bool:
        """
        Delete object from S3 bucket.
        
        Args:
            key (str): S3 object key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3.delete_object(
                Bucket=os.getenv('S3_BUCKET_NAME'),
                Key=key
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting object {key}: {str(e)}")
            return False 