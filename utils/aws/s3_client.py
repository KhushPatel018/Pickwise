"""
AWS S3 client utilities for the resume processor workflow.
"""
import logging
import json
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self, bucket_name: str = None):
        """
        Initialize S3 client.
        
        Args:
            bucket_name: Optional bucket name, will use default if not provided
        """
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name

    def batch_get_objects(self, s3_urls: List[str]) -> Dict[str, Any]:
        """
        Get multiple objects from S3 in a single batch request.
        
        Args:
            s3_urls: List of S3 URLs to fetch
            
        Returns:
            Dict[str, Any]: Dictionary mapping S3 URLs to their contents
            
        Raises:
            Exception: If any object cannot be fetched
        """
        try:
            result = {}
            for url in s3_urls:
                bucket, key = self._parse_s3_url(url)
                response = self.s3.get_object(Bucket=bucket, Key=key)
                result[url] = response
            return result
        except ClientError as e:
            logger.error(f"Failed to fetch objects from S3: {str(e)}")
            raise Exception(f"S3 batch get failed: {str(e)}")

    def save_analysis(self, key: str, analysis_data: Dict[str, Any]) -> bool:
        """
        Save analysis results to S3.
        
        Args:
            key: S3 key to save the analysis
            analysis_data: Analysis data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert analysis data to JSON with proper formatting
            json_data = json.dumps(analysis_data, indent=2)
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )
            
            logger.info(f"Successfully saved analysis to {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save analysis to S3: {str(e)}")
            return False

    def get_object(self, key: str) -> Dict[str, Any]:
        """
        Get a single object from S3.
        
        Args:
            key: S3 key to fetch
            
        Returns:
            Dict[str, Any]: Object contents
            
        Raises:
            Exception: If object cannot be fetched
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            logger.error(f"Failed to fetch object {key} from S3: {str(e)}")
            raise Exception(f"S3 get failed: {str(e)}")

    def put_object(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Put a single object to S3.
        
        Args:
            key: S3 key to save to
            data: Data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_data = json.dumps(data, indent=2)
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to put object {key} to S3: {str(e)}")
            return False

    def _parse_s3_url(self, url: str) -> tuple[str, str]:
        """
        Parse S3 URL into bucket and key.
        
        Args:
            url: S3 URL (s3://bucket/key)
            
        Returns:
            tuple[str, str]: (bucket, key)
            
        Raises:
            ValueError: If URL is invalid
        """
        try:
            # Remove s3:// prefix if present
            if url.startswith('s3://'):
                url = url[5:]
            
            # Split into bucket and key
            parts = url.split('/', 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid S3 URL format: {url}")
                
            return parts[0], parts[1]
            
        except Exception as e:
            logger.error(f"Failed to parse S3 URL {url}: {str(e)}")
            raise ValueError(f"Invalid S3 URL: {url}")

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
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting object {key} from bucket {self.bucket_name}: {str(e)}")
            return False 