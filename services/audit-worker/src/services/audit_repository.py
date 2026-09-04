"""
DynamoDB repository for audit record operations.
Handles all persistence logic for audit records.
"""

from typing import Optional, List
from boto3.dynamodb.conditions import Key, Attr
from src.logger import setup_logger, log_with_context
from src.config import Config
from src.context import app_context
from src.models.audit import AuditRecord
from src.exceptions import DynamoDBError

logger = setup_logger(__name__, Config.LOG_LEVEL)


class AuditRepository:
    """
    Data access object for audit records in DynamoDB.
    
    Handles all interactions with the audit table.
    DynamoDB schema:
    - PK: resource_id (incident_id)
    - SK: created_at#audit_id (allows chronological ordering)
    """

    def __init__(self):
        """Initialize repository with DynamoDB table reference."""
        self.table = app_context.get_audit_table()
        self.table_name = Config.AUDIT_TABLE_NAME

    def create_audit_record(self, record: AuditRecord) -> bool:
        """
        Persist an audit record to DynamoDB.

        Args:
            record: AuditRecord instance

        Returns:
            True if successfully created

        Raises:
            DynamoDBError: If put_item fails
        """
        try:
            item = record.to_dynamodb_item()

            self.table.put_item(Item=item)

            log_with_context(
                logger,
                "INFO",
                "Audit record created successfully",
                resource_id=record.resource_id,
                audit_id=record.audit_id,
                source_event_id=record.source_event_id,
                action=record.action,
                actor_id=record.actor_id,
            )

            return True

        except Exception as e:
            error_msg = f"Failed to create audit record: {str(e)}"
            log_with_context(
                logger,
                "ERROR",
                error_msg,
                resource_id=record.resource_id,
                error=str(e),
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )

    def get_records_by_resource(self, resource_id: str) -> List[AuditRecord]:
        """
        Retrieve all audit records for a specific resource.
        
        Results are sorted by created_at (ascending) due to sort key structure.

        Args:
            resource_id: Resource ID (e.g., incident_id)

        Returns:
            List of AuditRecord instances, sorted chronologically

        Raises:
            DynamoDBError: If query fails
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("resource_id").eq(resource_id)
            )

            records = []
            for item in response.get("Items", []):
                record = AuditRecord.from_dynamodb_item(item)
                records.append(record)

            log_with_context(
                logger,
                "INFO",
                f"Retrieved {len(records)} audit records",
                resource_id=resource_id,
            )

            return records

        except Exception as e:
            error_msg = f"Failed to query audit records: {str(e)}"
            log_with_context(
                logger,
                "ERROR",
                error_msg,
                resource_id=resource_id,
                error=str(e),
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )

    def record_exists_by_source_event(
        self, resource_id: str, source_event_id: str
    ) -> bool:
        """
        Check if an audit record already exists for a given source event.
        
        Used for idempotency: prevent duplicate records from same event.

        Args:
            resource_id: Resource ID (e.g., incident_id)
            source_event_id: Source event ID

        Returns:
            True if record exists, False otherwise

        Raises:
            DynamoDBError: If query fails
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("resource_id").eq(resource_id),
                FilterExpression=Attr("source_event_id").eq(source_event_id),
                ProjectionExpression="audit_id",
                Limit=1,
            )

            exists = len(response.get("Items", [])) > 0

            if exists:
                log_with_context(
                    logger,
                    "INFO",
                    "Audit record already exists for source event (idempotent)",
                    resource_id=resource_id,
                    source_event_id=source_event_id,
                )
            else:
                log_with_context(
                    logger,
                    "DEBUG",
                    "No existing audit record found for source event",
                    resource_id=resource_id,
                    source_event_id=source_event_id,
                )

            return exists

        except Exception as e:
            error_msg = f"Failed to check audit record idempotency: {str(e)}"
            log_with_context(
                logger,
                "ERROR",
                error_msg,
                resource_id=resource_id,
                source_event_id=source_event_id,
                error=str(e),
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )

    def get_record_count(self, resource_id: str) -> int:
        """
        Get the count of audit records for a resource.

        Args:
            resource_id: Resource ID (e.g., incident_id)

        Returns:
            Number of audit records

        Raises:
            DynamoDBError: If query fails
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("resource_id").eq(resource_id),
                Select="COUNT",
            )

            count = response.get("Count", 0)

            log_with_context(
                logger,
                "DEBUG",
                f"Audit record count for resource: {count}",
                resource_id=resource_id,
            )

            return count

        except Exception as e:
            error_msg = f"Failed to count audit records: {str(e)}"
            log_with_context(
                logger,
                "ERROR",
                error_msg,
                resource_id=resource_id,
                error=str(e),
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )
