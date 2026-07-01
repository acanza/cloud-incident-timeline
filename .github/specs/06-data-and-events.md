# Data and Events Specification

## DynamoDB tables

### incidents

Owner:

```text
incident-service
```

Primary key:

```text
PK: incident_id
```

Recommended fields:

```text
incident_id
title
description
status
severity
created_by
created_at
updated_at
```
### incident_timeline

Owner:

```text
timeline-service
```

Primary key:

```text
PK: incident_id
SK: created_at#event_id
```

Recommended fields:

```text
incident_id
event_id
event_type
message
created_by
created_at
```
### audit_logs

Owner:

```text
audit-worker
```

Primary key:

```text
PK: entity_id
SK: created_at#audit_id
``` 

Recommended fields:

```text
entity_id
audit_id
event_type
performed_by
old_value
new_value
created_at
```
## EventBridge

Create a custom event bus for project domain events.

Recommended event source:

```text
cloud-incident-timeline.incident-service
```

Required event types:

```text
IncidentCreated
IncidentStatusChanged
```

## Event example

```hcl
{
  "Source": "cloud-incident-timeline.incident-service",
  "DetailType": "IncidentCreated",
  "Detail": {
    "incident_id": "inc_123",
    "title": "API latency spike",
    "severity": "SEV2",
    "status": "OPEN",
    "created_by": "antonio@example.com",
    "created_at": "2026-06-30T10:00:00Z"
  }
}
```

## EventBridge to SQS

Create an EventBridge rule that forwards incident events to the audit SQS queue.

The audit worker consumes from the queue and writes audit records.
