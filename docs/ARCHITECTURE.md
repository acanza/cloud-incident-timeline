# Architecture

## Overview

**Cloud Incident Timeline** is a microservices learning project demonstrating:
- **Synchronous HTTP APIs** (REST on ALB)
- **Asynchronous event processing** (EventBridge + SQS)
- **NoSQL data persistence** (DynamoDB)
- **Infrastructure as Code** (Terraform on AWS)

Three independent services communicate via:
1. **HTTP** — Request/response between clients and services
2. **Events** — Pub/sub for incident lifecycle changes

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Internet Users                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
                ┌─────────────────────────┐
                │  Application Load       │
                │  Balancer (ALB)         │
                │  Port 80                │
                └─────────────────────────┘
                    ↓                   ↓
        ┌───────────────────┐  ┌───────────────────┐
        │ incident-service  │  │ timeline-service  │
        │ (HTTP, Port 8080) │  │ (HTTP, Port 8080) │
        │ ECS Fargate       │  │ ECS Fargate       │
        └───────────────────┘  └───────────────────┘
          ↓                           ↓
    [incidents]                [incident_timeline]
     DynamoDB                    DynamoDB
          │                           │
          └───────────┬───────────────┘
                      ↓
          ┌───────────────────────┐
          │   EventBridge         │
          │  (Custom Event Bus)   │
          └───────────────────────┘
                      ↓
          ┌───────────────────────┐
          │    SQS Queue          │
          │ (Audit Events)        │
          └───────────────────────┘
                      ↓
        ┌───────────────────────────┐
        │    audit-worker           │
        │    (Background Worker)    │
        │    ECS Fargate            │
        └───────────────────────────┘
                      ↓
                [audit_logs]
                 DynamoDB
```

---

## Services

### incident-service

**Type:** Synchronous HTTP API

**Responsibility:** Manage incident lifecycle (CRUD operations)

**Endpoints:**
- `POST /incidents` — Create incident, publish `IncidentCreated` event
- `GET /incidents` — List all incidents
- `GET /incidents/{id}` — Get incident details
- `PATCH /incidents/{id}` — Update status/severity, publish `IncidentStatusChanged` event
- `GET /health` — ALB health check

**Database:**
- Table: `incidents`
- PK: `incident_id`
- Fields: title, description, status, severity, created_at, updated_at, created_by

**IAM Permissions:**
- Read/Write to `incidents` table (DynamoDB)
- Publish to EventBridge

---

### timeline-service

**Type:** Synchronous HTTP API (Read-Heavy)

**Responsibility:** Provide chronological view of incident changes

**Endpoints:**
- `GET /incidents/{id}/timeline` — Query all timeline entries for incident (ordered by timestamp)
- `POST /incidents/{id}/timeline/comments` — Add manual comment entry
- `GET /health` — ALB health check

**Database:**
- Table: `incident_timeline`
- PK: `incident_id`, SK: `created_at#event_id`
- Fields: event_type, message, created_by, created_at

**Data Sources:**
- Consumes events from SQS → transforms to human-readable timeline entries
- Stores incident state changes as immutable timeline entries

**IAM Permissions:**
- Read/Write to `incident_timeline` table (DynamoDB)
- Receive/Delete from SQS

---

### audit-worker

**Type:** Asynchronous background worker

**Responsibility:** Log all incident changes for compliance/audit trails

**Process:**
1. Long-poll SQS for incident events (20s wait, batch of 10)
2. Parse event envelope
3. Check for duplicates (idempotency by `source_event_id`)
4. Extract action and entity details
5. Write to audit log
6. Delete message from queue

**Database:**
- Table: `audit_logs`
- PK: `entity_id`, SK: `created_at#audit_id`
- Fields: event_type, action, performed_by, old_value, new_value

**Graceful Shutdown:** Respects SIGTERM signal, completes in-flight messages

**IAM Permissions:**
- Read from SQS
- Read/Write to `audit_logs` table (DynamoDB)

---

## Data Flow

### Synchronous Flow (HTTP)

```
User Request
    ↓
ALB routes to incident-service:8080
    ↓
incident-service:
  1. Validate request
  2. Create/update incident in DynamoDB
  3. Publish event to EventBridge
  4. Return response (201/200)
    ↓
ALB returns response to user
```

**Latency:** ~100-200ms per request

---

### Asynchronous Flow (Event-Driven)

```
incident-service publishes event to EventBridge
    ↓
EventBridge rule: route incident.* events to SQS
    ↓
Event enqueued in SQS (standard queue)
    ↓
audit-worker long-polls SQS (WaitTime=20s, MaxMessages=10)
    ↓
audit-worker:
  1. Parse event
  2. Check idempotency (skip if duplicate)
  3. Create audit record
  4. Write to DynamoDB
  5. Delete message from queue
    ↓
Audit trail persisted
```

**Latency:** ~100ms-20s (depends on poll interval)

**Reliability:** Messages in SQS until successfully processed and deleted

---

### Timeline Flow (Event Processing)

```
incident-service publishes event
    ↓
EventBridge rule: route timeline.* events to SQS (second queue)
    ↓
timeline-service long-polls SQS
    ↓
timeline-service:
  1. Parse event
  2. Transform to human-readable message
  3. Create timeline entry
  4. Write to incident_timeline table
  5. Delete message from queue
    ↓
GET /incidents/{id}/timeline returns chronological entries
```

---

## Key Architectural Decisions

### 1. **Event-Driven for Audit Trail**
- **Why:** Decouples incident-service from audit-worker
- **Benefit:** Services remain independent; audit failures don't block incident operations
- **Trade-off:** Eventual consistency (audit log might lag a few seconds)

### 2. **SQS for Durability**
- **Why:** Ensures no events are lost between EventBridge and workers
- **Benefit:** Retries handled automatically; at-least-once delivery
- **Trade-off:** Requires idempotency checks (handled by `source_event_id`)

### 3. **DynamoDB On-Demand Pricing**
- **Why:** Learning project with unpredictable traffic
- **Benefit:** No capacity planning; pay only for what you use
- **Cost:** ~$1.25 per GB written (more expensive at scale)

### 4. **One Task Per Service (desired_count=1)**
- **Why:** Learning project, cost control
- **Benefit:** Minimal AWS charges (~$2-5/day)
- **Trade-off:** No high availability; single point of failure

### 5. **ALB for Routing**
- **Why:** Multiple HTTP services behind single endpoint
- **Benefit:** URL-based routing (`/incidents*` vs `/incidents/*/timeline*`)
- **Trade-off:** Additional ~$0.50/day ALB charge

### 6. **Immutable Timeline Entries**
- **Why:** Compliance requirement (audit trail cannot be altered)
- **Benefit:** Data integrity guaranteed
- **Implementation:** No UPDATE operations; only INSERT and DELETE

### 7. **Public Subnets Only (No NAT Gateway)**
- **Why:** Cost control
- **Benefit:** Saves ~$32/month
- **Trade-off:** Limited security isolation (acceptable for dev/learning)

---

## Scaling Considerations

To scale to production:

1. **High Availability**
   - Increase `desired_count` to 3+ per service
   - Use RDS with multi-AZ for relational data (if needed)
   - Add NAT Gateway for private subnets

2. **Performance**
   - Switch DynamoDB to provisioned capacity with autoscaling
   - Add ElastiCache for frequently queried timelines
   - Use CloudFront for static content

3. **Reliability**
   - Add SQS dead-letter queues for failed events
   - Implement circuit breakers between services
   - Add distributed tracing (X-Ray)

4. **Cost Optimization**
   - Use reserved ECS capacity
   - Implement DynamoDB autoscaling
   - Add CloudWatch cost anomaly detection

---

## Related Documentation

- [Deployment Guide](./DEPLOYMENT.md) — Step-by-step deployment
- [Destroy Guide](./DESTROY.md) — Cleanup procedures
- Service READMEs — API contracts and testing
  - [incident-service](../services/incident-service/README.md)
  - [timeline-service](../services/timeline-service/README.md)
  - [audit-worker](../services/audit-worker/README.md)
