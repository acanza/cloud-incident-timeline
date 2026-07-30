# Service Implementation Specs — Event-Driven Microservices

## Project

`cloud-incident-timeline`

## Objective

Implement the application logic for the project services using an event-driven architecture based on **Option B**:

```text
incident-service → EventBridge/SQS → timeline-service
incident-service → EventBridge/SQS → audit-worker
```

The goal is to avoid direct service-to-service calls between `incident-service`, `timeline-service`, and `audit-worker`.

Each service must own its own responsibility and communicate through events whenever possible.

---

# 1. Architecture Overview

## Services

The application contains three services:

```text
services/
├── incident-service/
├── timeline-service/
└── audit-worker/
```

## Responsibilities

```text
incident-service
→ Owns the current state of incidents.

timeline-service
→ Owns the visible history/timeline of incidents.

audit-worker
→ Owns internal audit records and event traceability.
```

## Communication model

The system must follow an asynchronous event-driven pattern.

```text
Client
  ↓
ALB
  ↓
incident-service
  ↓
DynamoDB
  ↓
EventBridge
  ↓
SQS queues
  ↓
timeline-service / audit-worker
```

The `incident-service` must not call `timeline-service` directly.

The `incident-service` must not call `audit-worker` directly.

The `timeline-service` should consume relevant domain events and materialize a readable incident timeline.

The `audit-worker` should consume relevant domain events and store audit records.

---

# 2. Service Summary

## 2.1 `incident-service`

The `incident-service` is an HTTP API service.

It manages the lifecycle and current state of incidents.

It is responsible for:

* Creating incidents.
* Listing incidents.
* Retrieving incidents by ID.
* Updating incident status.
* Updating incident severity.
* Publishing domain events when meaningful changes happen.

It owns the incident data model.

It writes incident records to DynamoDB.

It publishes events to EventBridge after successful state changes.

---

## 2.2 `timeline-service`

The `timeline-service` is an event consumer and optional HTTP API service.

It maintains a readable timeline for each incident.

It is responsible for:

* Consuming incident domain events.
* Converting those events into user-facing timeline entries.
* Persisting timeline entries in DynamoDB.
* Exposing an endpoint to query the timeline of a specific incident.

It should not own the current state of incidents.

It should not update incident records.

It should only store the historical sequence of events relevant to the incident timeline.

---

## 2.3 `audit-worker`

The `audit-worker` is a background worker.

It does not expose public HTTP endpoints.

It is responsible for:

* Consuming domain events.
* Creating internal audit records.
* Storing who did what, when, and on which resource.
* Supporting traceability and debugging.

It should not own incident state.

It should not own user-facing timeline data.

It should only process audit-related records.

---

# 3. Event-Driven Architecture

## 3.1 Event Bus

Use EventBridge as the central event bus.

EventBridge event bus name (from Terraform):

```text
cloud-incident-timeline-dev-event-bus
```

All domain events should be published by `incident-service` to EventBridge.

EventBridge rules should route events to the appropriate SQS queues.

---

## 3.2 Queues

**Current implementation (Terraform)**: Only audit queue is provisioned.

Audit queue (from Terraform):

```text
cloud-incident-timeline-dev-audit-queue
```

Audit dead-letter queue (from Terraform):

```text
cloud-incident-timeline-dev-audit-dlq
```

**Note**: `timeline-service` currently consumes from the same audit queue as `audit-worker` as a shared queue implementation. This requires careful handling to avoid duplicate processing. For production, consider provisioning a separate `timeline-events-queue`.

Current routing:

```text
EventBridge
└── cloud-incident-timeline-dev-audit-queue
    (consumed by both timeline-service and audit-worker)
```

---

## 3.3 Queue Implementation Note

**MVP Compromise**: The current Terraform infrastructure provisions only one audit queue shared between `timeline-service` and `audit-worker`. Both services consume from:

```text
cloud-incident-timeline-dev-audit-queue
```

This creates competing consumers—each message is processed by only one service, not both.

**For future enhancement**: Implement separate queues (one for timeline, one for audit) to ensure each service receives a copy of every event. This requires:

1. Creating `cloud-incident-timeline-dev-timeline-queue`
2. Creating EventBridge rule to route to both queues
3. Updating timeline-service to consume from its dedicated queue

**Current workaround**: Code must handle the fact that services compete for messages. Idempotency becomes critical—if a service crashes mid-processing, the message may be retried by either service.

---

# 4. Event Contracts

All events published to EventBridge must follow a consistent structure.

## 4.1 Base event envelope

Every event should use this shape:

```json
{
  "version": "1.0",
  "event_id": "uuid",
  "event_type": "IncidentCreated",
  "source": "incident-service",
  "occurred_at": "2026-07-30T08:00:00Z",
  "correlation_id": "uuid",
  "actor": {
    "user_id": "system-or-user-id",
    "email": "optional@example.com"
  },
  "data": {}
}
```

## 4.2 Required fields

| Field            | Required | Description                               |
| ---------------- | -------: | ----------------------------------------- |
| `version`        |      Yes | Event schema version.                     |
| `event_id`       |      Yes | Unique event identifier.                  |
| `event_type`     |      Yes | Domain event name.                        |
| `source`         |      Yes | Service that emitted the event.           |
| `occurred_at`    |      Yes | UTC timestamp.                            |
| `correlation_id` |      Yes | ID used to trace the full request flow.   |
| `actor`          |      Yes | User or system that triggered the action. |
| `data`           |      Yes | Event-specific payload.                   |

---

# 5. Domain Events

## 5.1 `IncidentCreated`

Emitted when a new incident is created.

```json
{
  "version": "1.0",
  "event_id": "evt-001",
  "event_type": "IncidentCreated",
  "source": "incident-service",
  "occurred_at": "2026-07-30T08:00:00Z",
  "correlation_id": "corr-001",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  },
  "data": {
    "incident_id": "inc-001",
    "title": "API latency spike",
    "description": "The public API is responding slowly",
    "severity": "HIGH",
    "status": "OPEN"
  }
}
```

Consumers:

```text
timeline-service
audit-worker
```

---

## 5.2 `IncidentStatusChanged`

Emitted when an incident status changes.

```json
{
  "version": "1.0",
  "event_id": "evt-002",
  "event_type": "IncidentStatusChanged",
  "source": "incident-service",
  "occurred_at": "2026-07-30T08:15:00Z",
  "correlation_id": "corr-002",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  },
  "data": {
    "incident_id": "inc-001",
    "previous_status": "OPEN",
    "new_status": "INVESTIGATING"
  }
}
```

Consumers:

```text
timeline-service
audit-worker
```

---

## 5.3 `IncidentSeverityChanged`

Emitted when an incident severity changes.

```json
{
  "version": "1.0",
  "event_id": "evt-003",
  "event_type": "IncidentSeverityChanged",
  "source": "incident-service",
  "occurred_at": "2026-07-30T08:25:00Z",
  "correlation_id": "corr-003",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  },
  "data": {
    "incident_id": "inc-001",
    "previous_severity": "MEDIUM",
    "new_severity": "HIGH"
  }
}
```

Consumers:

```text
timeline-service
audit-worker
```

---

## 5.4 `IncidentResolved`

Emitted when an incident is resolved.

```json
{
  "version": "1.0",
  "event_id": "evt-004",
  "event_type": "IncidentResolved",
  "source": "incident-service",
  "occurred_at": "2026-07-30T09:00:00Z",
  "correlation_id": "corr-004",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  },
  "data": {
    "incident_id": "inc-001",
    "previous_status": "INVESTIGATING",
    "new_status": "RESOLVED",
    "resolution_summary": "Database indexes were optimized"
  }
}
```

Consumers:

```text
timeline-service
audit-worker
```

---

## 5.5 `TimelineCommentAdded`

Emitted when a user adds a visible comment to an incident timeline.

This event may be emitted by `timeline-service` if the service exposes an HTTP endpoint for adding comments.

```json
{
  "version": "1.0",
  "event_id": "evt-005",
  "event_type": "TimelineCommentAdded",
  "source": "timeline-service",
  "occurred_at": "2026-07-30T08:40:00Z",
  "correlation_id": "corr-005",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  },
  "data": {
    "incident_id": "inc-001",
    "comment": "Backend team is investigating database metrics"
  }
}
```

Consumers:

```text
audit-worker
```

This event does not need to be consumed again by `timeline-service` if the comment has already been written by the same service.

---

# 6. Data Models

## 6.1 Incidents table

Owned by `incident-service`.

Table name (from Terraform):

```text
cloud-incident-timeline-dev-incidents
```

Recommended fields:

```json
{
  "incident_id": "inc-001",
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "HIGH",
  "status": "OPEN",
  "created_at": "2026-07-30T08:00:00Z",
  "updated_at": "2026-07-30T08:00:00Z"
}
```

Recommended partition key:

```text
PK: incident_id
```

Valid statuses:

```text
OPEN
INVESTIGATING
RESOLVED
CLOSED
```

Valid severities:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

---

## 6.2 Timeline table

Owned by `timeline-service`.

Table name (from Terraform):

```text
cloud-incident-timeline-dev-incident-timeline
```

Recommended fields:

```json
{
  "incident_id": "inc-001",
  "timeline_entry_id": "tl-001",
  "event_type": "IncidentCreated",
  "message": "Incident created with HIGH severity",
  "created_at": "2026-07-30T08:00:00Z",
  "source_event_id": "evt-001"
}
```

Recommended keys:

```text
PK: incident_id
SK: created_at#timeline_entry_id
```

This allows querying all timeline entries for a given incident ordered by time.

---

## 6.3 Audit table

Owned by `audit-worker`.

Table name (from Terraform):

```text
cloud-incident-timeline-dev-audit-logs
```

Recommended fields:

```json
{
  "audit_id": "audit-001",
  "event_id": "evt-001",
  "event_type": "IncidentCreated",
  "resource_type": "incident",
  "resource_id": "inc-001",
  "actor_user_id": "user-001",
  "actor_email": "user@example.com",
  "occurred_at": "2026-07-30T08:00:00Z",
  "processed_at": "2026-07-30T08:00:02Z",
  "source": "incident-service"
}
```

Recommended partition key:

```text
PK: audit_id
```

Optional global secondary index:

```text
GSI1PK: resource_id
GSI1SK: occurred_at
```

This would allow querying audit records by incident.

For the MVP, the GSI is optional.

---

# 7. HTTP API Contracts

## 7.1 `incident-service`

The `incident-service` must expose HTTP endpoints through the ALB.

### Health check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "incident-service"
}
```

---

### Create incident

```http
POST /incidents
```

Request:

```json
{
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "HIGH",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  }
}
```

Expected behavior:

1. Validate required fields.
2. Create a new `incident_id`.
3. Store the incident in the incidents table.
4. Publish `IncidentCreated` to EventBridge.
5. Return the created incident.

Response:

```json
{
  "incident_id": "inc-001",
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "HIGH",
  "status": "OPEN",
  "created_at": "2026-07-30T08:00:00Z",
  "updated_at": "2026-07-30T08:00:00Z"
}
```

---

### List incidents

```http
GET /incidents
```

Response:

```json
{
  "items": [
    {
      "incident_id": "inc-001",
      "title": "API latency spike",
      "severity": "HIGH",
      "status": "OPEN",
      "created_at": "2026-07-30T08:00:00Z",
      "updated_at": "2026-07-30T08:00:00Z"
    }
  ]
}
```

---

### Get incident by ID

```http
GET /incidents/{incident_id}
```

Response:

```json
{
  "incident_id": "inc-001",
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "HIGH",
  "status": "OPEN",
  "created_at": "2026-07-30T08:00:00Z",
  "updated_at": "2026-07-30T08:00:00Z"
}
```

If not found:

```json
{
  "message": "Incident not found"
}
```

HTTP status:

```text
404
```

---

### Update incident status

```http
PATCH /incidents/{incident_id}/status
```

Request:

```json
{
  "status": "INVESTIGATING",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  }
}
```

Expected behavior:

1. Retrieve current incident.
2. Validate new status.
3. If status has not changed, return the current incident without publishing an event.
4. If status changed, update the incident.
5. Publish `IncidentStatusChanged`.
6. If new status is `RESOLVED`, publish `IncidentResolved` instead of or in addition to `IncidentStatusChanged`.

Recommended rule for MVP:

```text
If new status is RESOLVED, publish only IncidentResolved.
For all other status changes, publish IncidentStatusChanged.
```

Response:

```json
{
  "incident_id": "inc-001",
  "status": "INVESTIGATING",
  "updated_at": "2026-07-30T08:15:00Z"
}
```

---

### Update incident severity

```http
PATCH /incidents/{incident_id}/severity
```

Request:

```json
{
  "severity": "CRITICAL",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  }
}
```

Expected behavior:

1. Retrieve current incident.
2. Validate new severity.
3. If severity has not changed, return the current incident without publishing an event.
4. If severity changed, update the incident.
5. Publish `IncidentSeverityChanged`.

Response:

```json
{
  "incident_id": "inc-001",
  "severity": "CRITICAL",
  "updated_at": "2026-07-30T08:25:00Z"
}
```

---

## 7.2 `timeline-service`

The `timeline-service` should expose HTTP endpoints through the ALB only for query and optional comment creation.

### Health check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "timeline-service"
}
```

---

### Get incident timeline

```http
GET /incidents/{incident_id}/timeline
```

Expected behavior:

1. Query timeline entries by `incident_id`.
2. Sort entries by creation time ascending.
3. Return readable timeline entries.

Response:

```json
{
  "incident_id": "inc-001",
  "items": [
    {
      "timeline_entry_id": "tl-001",
      "event_type": "IncidentCreated",
      "message": "Incident created with HIGH severity",
      "created_at": "2026-07-30T08:00:00Z"
    },
    {
      "timeline_entry_id": "tl-002",
      "event_type": "IncidentStatusChanged",
      "message": "Status changed from OPEN to INVESTIGATING",
      "created_at": "2026-07-30T08:15:00Z"
    }
  ]
}
```

---

### Add timeline comment

Optional for MVP, but useful for portfolio.

```http
POST /incidents/{incident_id}/timeline/comments
```

Request:

```json
{
  "comment": "Backend team is investigating database metrics",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  }
}
```

Expected behavior:

1. Validate the comment.
2. Store a timeline entry.
3. Publish `TimelineCommentAdded` to EventBridge.
4. Return the created timeline entry.

Response:

```json
{
  "timeline_entry_id": "tl-003",
  "incident_id": "inc-001",
  "event_type": "TimelineCommentAdded",
  "message": "Backend team is investigating database metrics",
  "created_at": "2026-07-30T08:40:00Z"
}
```

---

# 8. Event Consumer Behavior

## 8.1 `timeline-service` event consumer

The `timeline-service` must consume messages from `timeline-events-queue`.

It should process the following event types:

```text
IncidentCreated
IncidentStatusChanged
IncidentSeverityChanged
IncidentResolved
```

For each event, it should create one readable timeline entry.

### Message transformation rules

#### `IncidentCreated`

Input:

```json
{
  "event_type": "IncidentCreated",
  "data": {
    "incident_id": "inc-001",
    "severity": "HIGH",
    "status": "OPEN"
  }
}
```

Timeline message:

```text
Incident created with HIGH severity and OPEN status.
```

---

#### `IncidentStatusChanged`

Input:

```json
{
  "event_type": "IncidentStatusChanged",
  "data": {
    "incident_id": "inc-001",
    "previous_status": "OPEN",
    "new_status": "INVESTIGATING"
  }
}
```

Timeline message:

```text
Status changed from OPEN to INVESTIGATING.
```

---

#### `IncidentSeverityChanged`

Input:

```json
{
  "event_type": "IncidentSeverityChanged",
  "data": {
    "incident_id": "inc-001",
    "previous_severity": "MEDIUM",
    "new_severity": "HIGH"
  }
}
```

Timeline message:

```text
Severity changed from MEDIUM to HIGH.
```

---

#### `IncidentResolved`

Input:

```json
{
  "event_type": "IncidentResolved",
  "data": {
    "incident_id": "inc-001",
    "resolution_summary": "Database indexes were optimized"
  }
}
```

Timeline message:

```text
Incident resolved. Resolution: Database indexes were optimized.
```

If `resolution_summary` is missing:

```text
Incident resolved.
```

---

## 8.2 `audit-worker` event consumer

The `audit-worker` must consume messages from `audit-events-queue`.

It should process the following event types:

```text
IncidentCreated
IncidentStatusChanged
IncidentSeverityChanged
IncidentResolved
TimelineCommentAdded
```

For each event, it should create one audit record.

The audit record should include:

```text
audit_id
event_id
event_type
resource_type
resource_id
actor_user_id
actor_email
occurred_at
processed_at
source
correlation_id
```

### Resource mapping

| Event type                | Resource type       | Resource ID        |
| ------------------------- | ------------------- | ------------------ |
| `IncidentCreated`         | `incident`          | `data.incident_id` |
| `IncidentStatusChanged`   | `incident`          | `data.incident_id` |
| `IncidentSeverityChanged` | `incident`          | `data.incident_id` |
| `IncidentResolved`        | `incident`          | `data.incident_id` |
| `TimelineCommentAdded`    | `incident_timeline` | `data.incident_id` |

---

# 9. Idempotency

Consumers must be idempotent.

This is important because SQS can deliver the same message more than once.

## 9.1 Timeline idempotency

The `timeline-service` must avoid creating duplicate timeline entries for the same source event.

Recommended approach:

Store `source_event_id` in each timeline entry.

Before creating a new timeline entry, check whether an entry already exists for that `source_event_id`.

Better approach if supported by the table design:

Use `source_event_id` as part of a conditional write or maintain a separate processed-events table.

MVP approach:

```text
Use source_event_id in the timeline item and perform a conditional write where possible.
```

---

## 9.2 Audit idempotency

The `audit-worker` must avoid creating duplicate audit records for the same event.

Recommended approach:

Use the event ID as the audit record ID.

```text
audit_id = event_id
```

Then write using a conditional expression:

```text
Only insert if audit_id does not already exist.
```

This makes repeated processing safe.

---

# 10. Error Handling

## 10.1 API errors

HTTP services should return consistent JSON errors.

Recommended format:

```json
{
  "message": "Validation error",
  "details": [
    {
      "field": "severity",
      "error": "Invalid value"
    }
  ]
}
```

Use standard HTTP status codes:

| Scenario           | Status |
| ------------------ | -----: |
| Invalid input      |  `400` |
| Resource not found |  `404` |
| Conflict           |  `409` |
| Internal error     |  `500` |

---

## 10.2 Event processing errors

If a consumer fails to process a message, it should not delete the message from SQS.

The message should become visible again and be retried according to the queue redrive policy.

After the maximum receive count is reached, the message should be moved to the DLQ.

Each failed processing attempt should be logged with:

```text
event_id
event_type
correlation_id
error message
service name
```

---

# 11. Observability

Each service must produce structured logs.

Recommended log fields:

```json
{
  "timestamp": "2026-07-30T08:00:00Z",
  "level": "INFO",
  "service": "incident-service",
  "message": "Incident created",
  "correlation_id": "corr-001",
  "event_id": "evt-001",
  "incident_id": "inc-001"
}
```

## Required logging

### `incident-service`

Log:

* Incoming HTTP requests.
* Validation failures.
* DynamoDB writes.
* EventBridge publish attempts.
* EventBridge publish failures.
* Successful event publication.

### `timeline-service`

Log:

* Incoming HTTP requests.
* SQS messages received.
* Timeline entries created.
* Duplicate events skipped.
* Processing failures.

### `audit-worker`

Log:

* SQS messages received.
* Audit records created.
* Duplicate events skipped.
* Processing failures.

---

# 12. Environment Variables

## 12.1 `incident-service`

Required environment variables (from Terraform):

```text
AWS_REGION = aws region (e.g., us-east-1)
INCIDENTS_TABLE_NAME = cloud-incident-timeline-dev-incidents
EVENT_BUS_NAME = cloud-incident-timeline-dev-event-bus
```

Optional:

```text
SERVICE_NAME = incident-service (for logging)
LOG_LEVEL = INFO | DEBUG
```

Optional:

```text
LOG_LEVEL
```

---

## 12.2 `timeline-service`

Required environment variables (from Terraform):

```text
AWS_REGION = aws region (e.g., us-east-1)
TIMELINE_TABLE_NAME = cloud-incident-timeline-dev-incident-timeline
AUDIT_QUEUE_URL = https://sqs.<region>.amazonaws.com/<account>/cloud-incident-timeline-dev-audit-queue
```

**MVP Note**: `timeline-service` consumes from the same `AUDIT_QUEUE_URL` as `audit-worker`. Both services are competing consumers. Update to use a dedicated `TIMELINE_QUEUE_URL` once separate queue is provisioned.

`EVENT_BUS_NAME` is required only if the service implements `POST /incidents/{incident_id}/timeline/comments` and emits `TimelineCommentAdded`:

```text
EVENT_BUS_NAME = cloud-incident-timeline-dev-event-bus
```

Optional:

```text
SERVICE_NAME = timeline-service (for logging)
LOG_LEVEL = INFO | DEBUG
```

---

## 12.3 `audit-worker`

Required environment variables (from Terraform):

```text
AWS_REGION = aws region (e.g., us-east-1)
AUDIT_TABLE_NAME = cloud-incident-timeline-dev-audit-logs
AUDIT_QUEUE_URL = https://sqs.<region>.amazonaws.com/<account>/cloud-incident-timeline-dev-audit-queue
```

Optional:

```text
SERVICE_NAME = audit-worker (for logging)
LOG_LEVEL = INFO | DEBUG
```

---

# 13. IAM Requirements

## 13.1 `incident-service` task role

The ECS task role for `incident-service` must allow:

```text
dynamodb:PutItem
dynamodb:GetItem
dynamodb:UpdateItem
dynamodb:Scan or dynamodb:Query
events:PutEvents
```

Resources:

```text
Incidents DynamoDB table
EventBridge event bus
```

---

## 13.2 `timeline-service` task role

The ECS task role for `timeline-service` must allow:

```text
sqs:ReceiveMessage
sqs:DeleteMessage
sqs:GetQueueAttributes
dynamodb:PutItem
dynamodb:Query
```

If comment creation is implemented:

```text
events:PutEvents
```

Resources:

```text
Timeline SQS queue
Timeline DynamoDB table
EventBridge event bus, only if needed
```

---

## 13.3 `audit-worker` task role

The ECS task role for `audit-worker` must allow:

```text
sqs:ReceiveMessage
sqs:DeleteMessage
sqs:GetQueueAttributes
dynamodb:PutItem
```

Resources:

```text
Audit SQS queue
Audit DynamoDB table
```

---

# 14. Routing Expectations

## 14.1 ALB routing (from Terraform)

The ALB routes HTTP traffic using target groups.

Actual routing in Terraform:

```text
Target Group 1: incident-service (port 80)
  Health check: /health
  
Target Group 2: timeline-service (port 80)
  Health check: /health
```

**Note**: Actual path-based routing rules should be configured in the ALB listener rules. Currently, the ALB module in Terraform provisions the infrastructure but path routing may need manual configuration in AWS Console or additional Terraform rules.

Recommended path-based routing (to be implemented):

```text
Priority 10: /incidents/*/timeline* → timeline-service target group
Priority 20: /incidents*            → incident-service target group
```

The `audit-worker` should not be exposed through the ALB (worker only, no HTTP service).

---

# 15. Local Development Requirements

Each service should be runnable locally.

Each service should include:

```text
Dockerfile
.dockerignore
README.md
src/
```

Recommended commands:

```bash
docker build -t incident-service ./services/incident-service
docker build -t timeline-service ./services/timeline-service
docker build -t audit-worker ./services/audit-worker
```

Optional local execution:

```bash
docker run --env-file .env incident-service
docker run --env-file .env timeline-service
docker run --env-file .env audit-worker
```

Do not hardcode AWS resource names in the application code.

Use environment variables.

---

# 16. Implementation Order

Implement the services in this order.

## Step 1 — Shared conventions

Create shared conventions before implementing business logic:

* Event envelope structure.
* Correlation ID handling.
* Structured logging format.
* Error response format.
* Valid incident statuses.
* Valid incident severities.

These can be duplicated per service for MVP simplicity.

Avoid creating a shared internal library unless necessary.

---

## Step 2 — `incident-service`

Implement:

```text
GET /health
POST /incidents
GET /incidents
GET /incidents/{incident_id}
PATCH /incidents/{incident_id}/status
PATCH /incidents/{incident_id}/severity
```

Then verify:

```text
Incident is stored in DynamoDB.
Event is published to EventBridge.
Event reaches the expected SQS queues.
```

---

## Step 3 — `audit-worker`

Implement the SQS polling loop.

Process events from `audit-events-queue`.

Store audit records.

Then verify:

```text
Creating an incident produces one audit record.
Changing status produces one audit record.
Changing severity produces one audit record.
```

---

## Step 4 — `timeline-service` consumer

Implement the SQS polling loop.

Process events from `timeline-events-queue`.

Store timeline entries.

Then verify:

```text
Creating an incident produces one timeline entry.
Changing status produces one timeline entry.
Changing severity produces one timeline entry.
Resolving an incident produces one timeline entry.
```

---

## Step 5 — `timeline-service` HTTP API

Implement:

```text
GET /health
GET /incidents/{incident_id}/timeline
```

Optional:

```text
POST /incidents/{incident_id}/timeline/comments
```

Then verify:

```text
The timeline can be queried through the ALB.
```

---

# 17. Acceptance Criteria

The implementation is complete when all of the following are true.

## Incident creation

Given a valid request:

```http
POST /incidents
```

The system must:

```text
Create an incident in DynamoDB.
Publish IncidentCreated.
Create one timeline entry.
Create one audit record.
Return HTTP 201.
```

---

## Status change

Given a valid request:

```http
PATCH /incidents/{incident_id}/status
```

The system must:

```text
Update the incident status.
Publish IncidentStatusChanged or IncidentResolved.
Create one timeline entry.
Create one audit record.
Return HTTP 200.
```

---

## Severity change

Given a valid request:

```http
PATCH /incidents/{incident_id}/severity
```

The system must:

```text
Update the incident severity.
Publish IncidentSeverityChanged.
Create one timeline entry.
Create one audit record.
Return HTTP 200.
```

---

## Timeline query

Given an existing incident:

```http
GET /incidents/{incident_id}/timeline
```

The system must:

```text
Return timeline entries ordered by creation time.
Return HTTP 200.
```

---

## Worker behavior

Given a duplicated SQS message:

```text
timeline-service must not create duplicate timeline entries.
audit-worker must not create duplicate audit records.
```

---

# 18. Out of Scope for MVP

The following features are out of scope for the first implementation:

```text
Authentication and authorization
Cognito integration
Frontend application
CI/CD pipelines
Multi-environment deployment
Service discovery
App Mesh
Distributed tracing with X-Ray
Autoscaling policies
Secrets Manager
RDS
Complex event schema registry
Full replay mechanism
```

These can be added later as portfolio enhancements.

---

# 19. Recommended MVP Test Flow

Use the deployed ALB URL.

## 19.1 Create incident

```bash
curl -X POST "http://<alb-dns-name>/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API latency spike",
    "description": "The public API is responding slowly",
    "severity": "HIGH",
    "actor": {
      "user_id": "user-001",
      "email": "user@example.com"
    }
  }'
```

Expected:

```text
HTTP 201
Incident stored in DynamoDB
IncidentCreated event published
Timeline entry created
Audit record created
```

---

## 19.2 Change status

```bash
curl -X PATCH "http://<alb-dns-name>/incidents/<incident_id>/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "INVESTIGATING",
    "actor": {
      "user_id": "user-001",
      "email": "user@example.com"
    }
  }'
```

Expected:

```text
HTTP 200
Incident status updated
IncidentStatusChanged event published
Timeline entry created
Audit record created
```

---

## 19.3 Change severity

```bash
curl -X PATCH "http://<alb-dns-name>/incidents/<incident_id>/severity" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "CRITICAL",
    "actor": {
      "user_id": "user-001",
      "email": "user@example.com"
    }
  }'
```

Expected:

```text
HTTP 200
Incident severity updated
IncidentSeverityChanged event published
Timeline entry created
Audit record created
```

---

## 19.4 Query timeline

```bash
curl "http://<alb-dns-name>/incidents/<incident_id>/timeline"
```

Expected:

```text
HTTP 200
Timeline entries returned in chronological order
```

---

# 20. Design Principles

The implementation must follow these principles:

```text
Keep services independent.
Avoid direct service-to-service calls.
Use events for cross-service communication.
Each service owns its own data.
Use environment variables for infrastructure values.
Use structured logs.
Make consumers idempotent.
Prefer simple MVP implementation over unnecessary abstractions.
```

The final result should demonstrate practical knowledge of:

```text
ECS Fargate
Dockerized microservices
ALB path-based routing
DynamoDB
EventBridge
SQS
IAM task roles
Event-driven architecture
Asynchronous processing
Terraform-managed infrastructure
```
