"""
Unit tests for Phase 2 models and validators.
Run with: python -m pytest tests/test_phase2.py -v
"""

import pytest
from src.models.timeline import TimelineEntry
from src.models.event import (
    IncidentCreatedEvent,
    IncidentStatusChangedEvent,
    IncidentSeverityChangedEvent,
    IncidentResolvedEvent,
    ActorInfo,
)
from src.models.validators import EventValidator, TimelineEntryValidator
from src.models.transformer import EventTransformer


class TestTimelineEntry:
    """Tests for TimelineEntry model."""

    def test_create_timeline_entry(self):
        """Test creating a timeline entry."""
        entry = TimelineEntry(
            incident_id="inc-001",
            timeline_entry_id="tl-001",
            created_at="2026-07-30T08:00:00Z",
            message="Incident created with HIGH severity",
            event_type="IncidentCreated",
            source_event_id="evt-001",
        )

        assert entry.incident_id == "inc-001"
        assert entry.timeline_entry_id == "tl-001"
        assert entry.message == "Incident created with HIGH severity"

    def test_timeline_entry_to_dynamodb(self):
        """Test converting timeline entry to DynamoDB format."""
        entry = TimelineEntry(
            incident_id="inc-001",
            timeline_entry_id="tl-001",
            created_at="2026-07-30T08:00:00Z",
            message="Status changed",
            event_type="IncidentStatusChanged",
            source_event_id="evt-002",
        )

        dynamo_item = entry.to_dynamodb_item()

        assert dynamo_item["incident_id"] == "inc-001"
        assert "created_at__timeline_entry_id" in dynamo_item
        assert dynamo_item["source_event_id"] == "evt-002"

    def test_timeline_entry_from_dynamodb(self):
        """Test creating timeline entry from DynamoDB item."""
        dynamo_item = {
            "incident_id": "inc-001",
            "timeline_entry_id": "tl-001",
            "created_at": "2026-07-30T08:00:00Z",
            "message": "Test message",
            "event_type": "IncidentCreated",
            "source_event_id": "evt-001",
        }

        entry = TimelineEntry.from_dynamodb_item(dynamo_item)

        assert entry.incident_id == "inc-001"
        assert entry.message == "Test message"


class TestEventValidator:
    """Tests for EventValidator."""

    def test_validate_raw_event_missing_field(self):
        """Test validation fails when required field is missing."""
        raw_event = {
            "version": "1.0",
            "event_id": "evt-001",
            # Missing event_type
            "source": "incident-service",
        }

        is_valid, error = EventValidator.validate_raw_event(raw_event)
        assert not is_valid
        assert "event_type" in error

    def test_validate_raw_event_valid(self):
        """Test validation passes for valid event."""
        raw_event = {
            "version": "1.0",
            "event_id": "evt-001",
            "event_type": "IncidentCreated",
            "source": "incident-service",
            "occurred_at": "2026-07-30T08:00:00Z",
            "correlation_id": "corr-001",
            "actor": {"user_id": "user-001"},
            "data": {"incident_id": "inc-001"},
        }

        is_valid, error = EventValidator.validate_raw_event(raw_event)
        assert is_valid
        assert error is None

    def test_is_consumable_event(self):
        """Test checking if event type is consumable."""
        assert EventValidator.is_consumable_event("IncidentCreated")
        assert EventValidator.is_consumable_event("IncidentStatusChanged")
        assert EventValidator.is_consumable_event("IncidentSeverityChanged")
        assert EventValidator.is_consumable_event("IncidentResolved")
        assert not EventValidator.is_consumable_event("UnknownEvent")

    def test_parse_event_incident_created(self):
        """Test parsing IncidentCreated event."""
        raw_event = {
            "version": "1.0",
            "event_id": "evt-001",
            "event_type": "IncidentCreated",
            "source": "incident-service",
            "occurred_at": "2026-07-30T08:00:00Z",
            "correlation_id": "corr-001",
            "actor": {"user_id": "user-001", "email": "user@example.com"},
            "data": {
                "incident_id": "inc-001",
                "title": "API latency",
                "severity": "HIGH",
                "status": "OPEN",
            },
        }

        event = EventValidator.parse_event(raw_event)
        assert isinstance(event, IncidentCreatedEvent)
        assert event.data.incident_id == "inc-001"
        assert event.data.severity == "HIGH"


class TestTimelineEntryValidator:
    """Tests for TimelineEntryValidator."""

    def test_validate_timeline_entry_valid(self):
        """Test validation passes for valid timeline entry."""
        entry = {
            "incident_id": "inc-001",
            "timeline_entry_id": "tl-001",
            "created_at": "2026-07-30T08:00:00Z",
            "message": "Status changed",
            "event_type": "IncidentStatusChanged",
            "source_event_id": "evt-002",
        }

        is_valid, error = TimelineEntryValidator.validate_timeline_entry(entry)
        assert is_valid
        assert error is None

    def test_validate_timeline_entry_missing_message(self):
        """Test validation fails when message is missing."""
        entry = {
            "incident_id": "inc-001",
            "timeline_entry_id": "tl-001",
            "created_at": "2026-07-30T08:00:00Z",
            # Missing message
            "event_type": "IncidentCreated",
            "source_event_id": "evt-001",
        }

        is_valid, error = TimelineEntryValidator.validate_timeline_entry(entry)
        assert not is_valid

    def test_validate_idempotency_key_valid(self):
        """Test validation passes for valid idempotency key."""
        is_valid, error = TimelineEntryValidator.validate_idempotency_key("evt-001")
        assert is_valid
        assert error is None

    def test_validate_idempotency_key_invalid(self):
        """Test validation fails for invalid idempotency key."""
        is_valid, error = TimelineEntryValidator.validate_idempotency_key("")
        assert not is_valid


class TestEventTransformer:
    """Tests for EventTransformer."""

    def test_transform_incident_created(self):
        """Test transforming IncidentCreated event."""
        event = IncidentCreatedEvent(
            version="1.0",
            event_id="evt-001",
            source="incident-service",
            occurred_at="2026-07-30T08:00:00Z",
            correlation_id="corr-001",
            actor=ActorInfo(user_id="user-001"),
            data={
                "incident_id": "inc-001",
                "title": "API latency",
                "severity": "HIGH",
                "status": "OPEN",
            },
        )

        message = EventTransformer.transform_incident_created(event)
        assert "HIGH" in message
        assert "OPEN" in message
        assert "Incident created" in message

    def test_transform_status_changed(self):
        """Test transforming IncidentStatusChanged event."""
        event = IncidentStatusChangedEvent(
            version="1.0",
            event_id="evt-002",
            source="incident-service",
            occurred_at="2026-07-30T08:15:00Z",
            correlation_id="corr-002",
            actor=ActorInfo(user_id="user-001"),
            data={
                "incident_id": "inc-001",
                "previous_status": "OPEN",
                "new_status": "INVESTIGATING",
            },
        )

        message = EventTransformer.transform_status_changed(event)
        assert "OPEN" in message
        assert "INVESTIGATING" in message
        assert "Status changed" in message

    def test_transform_incident_resolved_with_summary(self):
        """Test transforming IncidentResolved with resolution summary."""
        event = IncidentResolvedEvent(
            version="1.0",
            event_id="evt-004",
            source="incident-service",
            occurred_at="2026-07-30T08:30:00Z",
            correlation_id="corr-004",
            actor=ActorInfo(user_id="user-001"),
            data={
                "incident_id": "inc-001",
                "resolution_summary": "Database indexes optimized",
            },
        )

        message = EventTransformer.transform_incident_resolved(event)
        assert "Incident resolved" in message
        assert "Database indexes optimized" in message

    def test_transform_incident_resolved_without_summary(self):
        """Test transforming IncidentResolved without resolution summary."""
        event = IncidentResolvedEvent(
            version="1.0",
            event_id="evt-004",
            source="incident-service",
            occurred_at="2026-07-30T08:30:00Z",
            correlation_id="corr-004",
            actor=ActorInfo(user_id="user-001"),
            data={"incident_id": "inc-001"},
        )

        message = EventTransformer.transform_incident_resolved(event)
        assert message == "Incident resolved."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
