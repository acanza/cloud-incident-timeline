"""Incident repository for DynamoDB persistence."""

import os
import json
import boto3
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..logger import get_structured_logger
from ..models.incident import Incident

logger = get_structured_logger(__name__, service_name="incident-service")


class IncidentRepository:
    """Repository for incident persistence in DynamoDB."""
    
    def __init__(self):
        """Initialize repository with DynamoDB client."""
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'eu-west-3'))
        self.table_name = os.getenv('INCIDENTS_TABLE_NAME', 'cloud-incident-timeline-dev-incidents')
        self.timeline_table_name = os.getenv('TIMELINE_TABLE_NAME', 'cloud-incident-timeline-dev-incident-timeline')
        
        try:
            self.table = self.dynamodb.Table(self.table_name)
            self.timeline_table = self.dynamodb.Table(self.timeline_table_name)
            logger.info(
                "Incident repository initialized",
                extra={
                    'incidents_table': self.table_name,
                    'timeline_table': self.timeline_table_name
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize DynamoDB tables: {str(e)}",
                extra={'exception_type': type(e).__name__}
            )
            raise
    
    def create_incident(self, incident: Incident) -> bool:
        """
        Create a new incident in DynamoDB.
        
        Args:
            incident: Incident object to persist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Write incident to incidents table
            self.table.put_item(
                Item={
                    'incident_id': incident.incident_id,
                    'title': incident.title,
                    'description': incident.description,
                    'severity': incident.severity,
                    'status': incident.status,
                    'created_at': incident.created_at,
                    'updated_at': incident.updated_at
                }
            )
            
            logger.info(
                "Incident created in DynamoDB",
                extra={'incident_id': incident.incident_id}
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to create incident: {str(e)}",
                extra={
                    'incident_id': incident.incident_id,
                    'exception_type': type(e).__name__
                }
            )
            return False
    
    def create_timeline_event(
        self,
        incident_id: str,
        event_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        created_at: str
    ) -> bool:
        """
        Create a timeline event for an incident.
        
        Args:
            incident_id: Incident identifier
            event_id: Unique event identifier
            event_type: Type of event (e.g., 'IncidentCreated')
            event_data: Event data payload
            created_at: Event creation timestamp
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.timeline_table.put_item(
                Item={
                    'incident_id': incident_id,
                    'created_at': created_at,
                    'event_id': event_id,
                    'event_type': event_type,
                    'event_data': json.dumps(event_data) if isinstance(event_data, dict) else event_data
                }
            )
            
            logger.info(
                "Timeline event created",
                extra={
                    'incident_id': incident_id,
                    'event_type': event_type,
                    'event_id': event_id
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to create timeline event: {str(e)}",
                extra={
                    'incident_id': incident_id,
                    'event_type': event_type,
                    'exception_type': type(e).__name__
                }
            )
            return False
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """
        Get an incident by ID.
        
        Args:
            incident_id: Incident identifier
            
        Returns:
            Incident object or None if not found
        """
        try:
            response = self.table.get_item(Key={'incident_id': incident_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            return Incident(
                incident_id=item['incident_id'],
                title=item['title'],
                description=item['description'],
                severity=item['severity'],
                status=item['status'],
                created_at=item['created_at'],
                updated_at=item['updated_at']
            )
            
        except Exception as e:
            logger.error(
                f"Failed to get incident: {str(e)}",
                extra={
                    'incident_id': incident_id,
                    'exception_type': type(e).__name__
                }
            )
            return None
    
    def list_incidents(self, limit: int = 100) -> List[Incident]:
        """
        List all incidents.
        
        Args:
            limit: Maximum number of incidents to return
            
        Returns:
            List of incident objects
        """
        try:
            response = self.table.scan(Limit=limit)
            
            incidents = []
            for item in response.get('Items', []):
                incident = Incident(
                    incident_id=item['incident_id'],
                    title=item['title'],
                    description=item['description'],
                    severity=item['severity'],
                    status=item['status'],
                    created_at=item['created_at'],
                    updated_at=item['updated_at']
                )
                incidents.append(incident)
            
            logger.debug(
                "Listed incidents",
                extra={'count': len(incidents)}
            )
            return incidents
            
        except Exception as e:
            logger.error(
                f"Failed to list incidents: {str(e)}",
                extra={'exception_type': type(e).__name__}
            )
            return []
    
    def update_incident_status(self, incident_id: str, new_status: str) -> bool:
        """
        Update incident status.
        
        Args:
            incident_id: Incident identifier
            new_status: New status value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key={'incident_id': incident_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': new_status,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            logger.info(
                "Incident status updated",
                extra={
                    'incident_id': incident_id,
                    'new_status': new_status
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to update incident status: {str(e)}",
                extra={
                    'incident_id': incident_id,
                    'exception_type': type(e).__name__
                }
            )
            return False
    
    def update_incident_severity(self, incident_id: str, new_severity: str) -> bool:
        """
        Update incident severity.
        
        Args:
            incident_id: Incident identifier
            new_severity: New severity value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key={'incident_id': incident_id},
                UpdateExpression='SET severity = :severity, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':severity': new_severity,
                    ':updated_at': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            logger.info(
                "Incident severity updated",
                extra={
                    'incident_id': incident_id,
                    'new_severity': new_severity
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to update incident severity: {str(e)}",
                extra={
                    'incident_id': incident_id,
                    'exception_type': type(e).__name__
                }
            )
            return False
