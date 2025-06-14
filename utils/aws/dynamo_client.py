"""
DynamoDB client for AWS operations.
"""
import boto3
import os
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError
from ..config import load_config

logger = logging.getLogger(__name__)

class DynamoClient:
    def __init__(self):
        """Initialize DynamoDB client with AWS credentials from environment variables."""
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

        # Initialize DynamoDB client
        self.dynamo = session.client('dynamodb')
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME')
        logger.info("DynamoDB client initialized successfully")

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get an item from DynamoDB.
        
        Args:
            key: Primary key of the item to get
            
        Returns:
            Dict containing item data or None if not found
        """
        try:
            response = self.dynamo.get_item(
                TableName=self.table_name,
                Key=key
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get item from DynamoDB: {str(e)}")
            return None

    def put_item(self, item: Dict[str, Any]) -> bool:
        """
        Put an item in DynamoDB.
        
        Args:
            item: Item to put
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.dynamo.put_item(
                TableName=self.table_name,
                Item=item
            )
            return True
        except Exception as e:
            logger.error(f"Failed to put item in DynamoDB: {str(e)}")
            return False

    def update_item(self, key: Dict[str, Any], update_expression: str, expression_values: Dict[str, Any]) -> bool:
        """
        Update an item in DynamoDB.
        
        Args:
            key: Primary key of the item to update
            update_expression: Update expression
            expression_values: Expression attribute values
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.dynamo.update_item(
                TableName=self.table_name,
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update item in DynamoDB: {str(e)}")
            return False

    def delete_item(self, key: Dict[str, Any]) -> bool:
        """
        Delete an item from DynamoDB.
        
        Args:
            key: Primary key of the item to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.dynamo.delete_item(
                TableName=self.table_name,
                Key=key
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete item from DynamoDB: {str(e)}")
            return False

    def query(self, key_condition_expression: str, 
             expression_values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query items from DynamoDB table.
        
        Args:
            key_condition_expression (str): Key condition expression
            expression_values (Dict[str, Any]): Expression attribute values
            
        Returns:
            List[Dict[str, Any]]: List of matching items
        """
        try:
            response = self.dynamo.query(
                TableName=self.table_name,
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=expression_values
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error querying table {self.table_name}: {str(e)}")
            return []