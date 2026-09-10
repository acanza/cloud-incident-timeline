"""Event publishing service for timeline-service."""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from ..constants import SERVICE_NAME
from ..context import get_correlation_id
from ..logger import get_structured_logger


logger = get_structured_logger(__name__, service_name=SERVICE_NAME)

# Event schema version
EVENT_SCHEMA_VERSION = "1.0"


class EventPublisher:
    """Service for publishing domain events from timeline-service to EventBridge."""
    
    def __init__(self):
        """Initialize EventPublisher with boto3 client and configuration."""
        self.events_client = boto3.client('events')
        self.event_bus_name = os.getenv('EVENT_BUS_NAME', 'cloud-incident-timeline-dev-event-bus')
        # Source must match EventBridge rules configured in infrastructure
        self.event_source = f"cloud-incident-timeline.{SERVICE_NAME}"
    
    def publish_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        actor_user_id: str,
        actor_email: Optional[str] = None
    ) -> str:
        """Publish an event to EventBridge.
        
        Args:
            event_type: Type of event (e.g., 'TimelineCommentAdded')
            event_data: Event payload data
            actor_user_id: User ID of the actor
            actor_email: Email of the actor (optional)
        
        Returns:
            Event ID
        
        Raises:
            ClientError: If EventBridge PutEvents fails
        """
        import uuid
        
        event_id = f"evt-{uuid.uuid4().hex[:12]}"
        correlation_id = get_correlation_id()
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Build event envelope with standard structure
        event_envelope = {
            "version": EVENT_SCHEMA_VERSION,
            "event_id": event_id,
            "event_type": event_type,
            "source": SERVICE_NAME,
            "occurred_at": now,
            "correlation_id": correlation_id,
            "actor": {
                "user_id": actor_user_id,
                "email": actor_email
            },
            "data": event_data
        }
        
        try:
            # Publish to EventBridge
            response = self.events_client.put_events(
                Entries=[
                    {
                        'Source': self.event_source,
                        'DetailType': event_type,  # e.g., "TimelineCommentAdded"
                        'Detail': json.dumps(event_envelope),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            # Check if the event was successfully published
            if response.get('FailedEntryCount', 0) > 0:
                error_msg = response.get('Entries', [{}])[0].get('ErrorMessage', 'Unknown error')
                logger.error(
                    f"Failed to publish event to EventBridge: {error_msg}",
                    extra={
                        'event_id': event_id,
                        'event_type': event_type,
                        'error': error_msg
                    }
                )
                raise ClientError(
                    {'Error': {'Code': 'EventBridgePublishError', 'Message': error_msg}},
                    'PutEvents'
                )
            
            # Log successful publication
            logger.info(
                f"Event published to EventBridge: {event_type}",
                extra={
                    'event_id': event_id,
                    'event_type': event_type,
                    'correlation_id': correlation_id,
                    'actor_user_id': actor_user_id,
                    'event_bus': self.event_bus_name
                }
            )
            
            return event_id
            
        except ClientError as e:
            logger.error(
                f"ClientError publishing event to EventBridge: {e}",
                extra={
                    'event_id': event_id,
                    'event_type': event_type,
                    'correlation_id': correlation_id,
                    'error_code': e.response.get('Error', {}).get('Code'),
                    'error_message': e.response.get('Error', {}).get('Message')
                }
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error publishing event to EventBridge: {e}",
                extra={
                    'event_id': event_id,
                    'event_type': event_type,
                    'correlation_id': correlation_id,
                    'error_type': type(e).__name__
                }
            )
            raise


# Global event publisher instance
event_publisher = EventPublisher()
