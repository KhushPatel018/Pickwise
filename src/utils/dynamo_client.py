"""
DynamoDB client for AWS operations.
"""
import boto3
import os
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError
from utils.config import load_config

logger = logging.getLogger(__name__)

class DynamoClient:
    def __init__(self):
        """Initialize DynamoDB client with AWS credentials from environment variables."""
        # Load environment configuration
        load_config()
        
        aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME')
        
        # Use high-level resource for dict support. Session is optional unless you want custom creds.
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')
        if aws_access_key and aws_secret_key:
            session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                aws_session_token=aws_session_token,
                region_name=aws_region
            )
            self.dynamo = session.resource('dynamodb', region_name=aws_region)
        else:
            # Will use default credential chain (works in Lambda, EC2, etc)
            self.dynamo = boto3.resource('dynamodb', region_name=aws_region)
        
        self.table = self.dynamo.Table(self.table_name)
        logger.info(f"DynamoDB client initialized successfully for table: {self.table_name}")

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get an item from DynamoDB.
        Args:
            key: Primary key of the item to get
        Returns:
            Dict containing item data or None if not found
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            logger.error(f"ClientError in get_item: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.exception("Failed to get item from DynamoDB")
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
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"ClientError in put_item: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.exception("Failed to put item in DynamoDB")
            return False

    def update_item(self, key: Dict[str, Any], update_expression: str, expression_values: Dict[str, Any], expression_attribute_names: Dict[str, str]) -> bool:
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
            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_attribute_names
            )
            return True
        except ClientError as e:
            logger.error(f"ClientError in update_item: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.exception("Failed to update item in DynamoDB")
            return False
