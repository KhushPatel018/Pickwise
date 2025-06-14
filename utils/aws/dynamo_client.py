"""
DynamoDB client utility for handling database operations.
"""
import logging
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DynamoClient:
    def __init__(self, table_name: str):
        """
        Initialize DynamoDB client with table name.
        
        Args:
            table_name (str): Name of the DynamoDB table
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get item from DynamoDB table.
        
        Args:
            key (Dict[str, Any]): Primary key of the item
            
        Returns:
            Optional[Dict[str, Any]]: Item data or None if error
        """
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting item from table {self.table.name}: {str(e)}")
            return None

    def put_item(self, item: Dict[str, Any]) -> bool:
        """
        Put item in DynamoDB table.
        
        Args:
            item (Dict[str, Any]): Item to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"Error putting item in table {self.table.name}: {str(e)}")
            return False

    def update_item(self, key: Dict[str, Any], update_expression: str, 
                   expression_values: Dict[str, Any]) -> bool:
        """
        Update item in DynamoDB table.
        
        Args:
            key (Dict[str, Any]): Primary key of the item
            update_expression (str): Update expression
            expression_values (Dict[str, Any]): Expression attribute values
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except ClientError as e:
            logger.error(f"Error updating item in table {self.table.name}: {str(e)}")
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
            response = self.table.query(
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=expression_values
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error querying table {self.table.name}: {str(e)}")
            return []

def update_candidate_status(
    dynamo_client,
    candidate_id: str,
    status: str,
    message: str,
    score: float
) -> None:
    """
    Update candidate status in DynamoDB.
    
    Args:
        dynamo_client: DynamoDB client instance
        candidate_id: Candidate ID
        status: Final status
        message: Status message
        score: Final score
    """
    try:
        dynamo_client.update_item(
            key={'candidate_id': candidate_id},
            update_expression='SET #status = :status, message = :message, final_score = :score',
            expression_values={
                ':status': status,
                ':message': message,
                ':score': score
            }
        )
    except Exception as e:
        logger.error(f"Failed to update final status in database: {str(e)}")
        raise 