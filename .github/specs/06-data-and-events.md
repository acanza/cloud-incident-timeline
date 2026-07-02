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

## EventBridge and SQS Defaults

The project must create one custom EventBridge bus.

Default bus name:

```text
cloud-incident-timeline-dev-event-bus
```

Name pattern:

```text
${project_name}-${environment}-event-bus
```

The `incident-service` must publish events using this source:

```text
cloud-incident-timeline.incident-service
```

Required event types:

```text
IncidentCreated
IncidentStatusChanged
```

Create one EventBridge rule to route incident domain events to the audit queue.

Default rule name:

```text
cloud-incident-timeline-dev-audit-events-rule
```

The rule must match:

```json
{
  "source": ["cloud-incident-timeline.incident-service"],
  "detail-type": ["IncidentCreated", "IncidentStatusChanged"]
}
```

Create one SQS queue for audit events.

Default queue name:

```text
cloud-incident-timeline-dev-audit-queue
```

Create one SQS dead-letter queue for audit processing failures.

Default DLQ name:

```text
cloud-incident-timeline-dev-audit-dlq
```

Recommended redrive policy:

```hcl
max_receive_count = 3
```

Do not configure a separate EventBridge target DLQ in v0.1.


## EventBridge to SQS

Create an EventBridge rule that forwards incident events to the audit SQS queue.

The audit worker consumes from the queue and writes audit records.
