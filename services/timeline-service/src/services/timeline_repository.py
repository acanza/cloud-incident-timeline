"""
DynamoDB repository for timeline operations.
Handles all persistence logic for timeline entries.
"""

from typing import Optional, List
from boto3.dynamodb.conditions import Key, Attr
from src.logger import setup_logger
from src.config import Config
from src.context import app_context
from src.models.timeline import TimelineEntry
from src.exceptions import DynamoDBError

logger = setup_logger(__name__, Config.LOG_LEVEL)


class TimelineRepository:
    """
    Data access object for timeline entries in DynamoDB.
    
    Handles all interactions with the timeline table.
    """

    def __init__(self):
        """Initialize repository with DynamoDB table reference."""
        self.table = app_context.get_timeline_table()
        self.table_name = Config.TIMELINE_TABLE_NAME

    def create_entry(self, entry: TimelineEntry) -> bool:
        """
        Persist a timeline entry to DynamoDB.

        Args:
            entry: TimelineEntry instance

        Returns:
            True if successfully created

        Raises:
            DynamoDBError: If put_item fails
        """
        try:
            item = entry.to_dynamodb_item()

            self.table.put_item(Item=item)

            logger.info(
                f"Timeline entry created successfully",
                extra={
                    "incident_id": entry.incident_id,
                    "timeline_entry_id": entry.timeline_entry_id,
                    "source_event_id": entry.source_event_id,
                },
            )

            return True

        except Exception as e:
            error_msg = f"Failed to create timeline entry: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "incident_id": entry.incident_id,
                    "error": str(e),
                },
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )

    def get_entries_by_incident(self, incident_id: str) -> List[TimelineEntry]:
        """
        Retrieve all timeline entries for a specific incident.
        
        Results are sorted by created_at (ascending) due to sort key structure.

        Args:
            incident_id: Incident ID

        Returns:
            List of TimelineEntry instances, sorted chronologically

        Raises:
            DynamoDBError: If query fails
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("incident_id").eq(incident_id)
            )

            entries = []
            for item in response.get("Items", []):
                entry = TimelineEntry.from_dynamodb_item(item)
                entries.append(entry)

            logger.info(
                f"Retrieved {len(entries)} timeline entries",
                extra={"incident_id": incident_id},
            )

            return entries

        except Exception as e:
            error_msg = f"Failed to query timeline entries: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "incident_id": incident_id,
                    "error": str(e),
                },
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )

    def entry_exists_by_source_event(self, incident_id: str, source_event_id: str) -> bool:
        """
        Check if a timeline entry already exists for a given source event.
        
        Used for idempotency: prevent duplicate entries from same event.

        Args:
            incident_id: Incident ID
            source_event_id: Source event ID

        Returns:
            True if entry exists, False otherwise

        Raises:
            DynamoDBError: If query fails
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("incident_id").eq(incident_id),
                FilterExpression=Attr("source_event_id").eq(source_event_id),
                ProjectionExpression="timeline_entry_id",
                Limit=1,
            )

            exists = len(response.get("Items", [])) > 0

            if exists:
                logger.info(
                    f"Timeline entry already exists for source event (idempotent)",
                    extra={
                        "incident_id": incident_id,
                        "source_event_id": source_event_id,
                    },
                )
            else:
                logger.debug(
                    f"No existing timeline entry for source event",
                    extra={
                        "incident_id": incident_id,
                        "source_event_id": source_event_id,
                    },
                )

            return exists

        except Exception as e:
            error_msg = f"Failed to check entry existence: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "incident_id": incident_id,
                    "source_event_id": source_event_id,
                    "error": str(e),
                },
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )

    def get_entry_count_by_incident(self, incident_id: str) -> int:
        """
        Get the count of timeline entries for an incident.

        Args:
            incident_id: Incident ID

        Returns:
            Number of entries for this incident

        Raises:
            DynamoDBError: If query fails
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key("incident_id").eq(incident_id),
                Select="COUNT",
            )

            count = response.get("Count", 0)

            logger.debug(
                f"Timeline entry count for incident",
                extra={
                    "incident_id": incident_id,
                    "count": count,
                },
            )

            return count

        except Exception as e:
            error_msg = f"Failed to count entries: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "incident_id": incident_id,
                    "error": str(e),
                },
            )
            raise DynamoDBError(
                error_msg,
                resource=self.table_name,
            )
