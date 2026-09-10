# Audit Worker

Background service for processing incident events and maintaining audit trails. Consumes events from SQS queue and persists audit records to DynamoDB with idempotency guarantees.

**Type:** Async SQS consumer  
**Database:** DynamoDB (audit_logs table)  
**Deployment:** ECS/Fargate (256 CPU / 512 MB)

## Quick Start

### Prerequisites

- Python 3.9+
- AWS credentials configured
- DynamoDB table: `cloud-incident-timeline-dev-audit-logs`
- SQS queue: `cloud-incident-timeline-dev-audit-queue`

### Setup

```bash
cd services/audit-worker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your AWS settings
```

### Run

```bash
python3 -m src.main
```

## Event Processing

### Supported Events

| Event | Action | Target |
|-------|--------|--------|
| `IncidentCreated` | `CREATED` | audit_logs |
| `IncidentStatusChanged` | `STATUS_CHANGED` | audit_logs |
| `IncidentSeverityChanged` | `SEVERITY_CHANGED` | audit_logs |
| `IncidentResolved` | `RESOLVED` | audit_logs |

### Flow

1. Long-poll SQS (10 msgs, 20s wait)
2. Parse event envelope
3. Check idempotency (by `source_event_id`)
4. Write audit record to DynamoDB
5. Delete message on success
6. Retry on error (leave in queue)

## Data Model

**Table:** `cloud-incident-timeline-dev-audit-logs`

| Field | Type | Purpose |
|-------|------|---------|
| `resource_id` | String | PK (incident_id) |
| `created_at#audit_id` | String | SK (timestamp + ID) |
| `event_type` | String | Original event type |
| `action` | String | Normalized action |
| `performed_by` | String | User who triggered |
| `source_event_id` | String | For idempotency check |
| `details` | Map | Event-specific data |

## Configuration

```bash
# Required
AWS_REGION=eu-west-3
AUDIT_TABLE_NAME=cloud-incident-timeline-dev-audit-logs
AUDIT_QUEUE_URL=https://sqs.eu-west-3.amazonaws.com/.../audit-queue

# Optional
SERVICE_NAME=audit-worker
LOG_LEVEL=INFO
```

## Testing

```bash
# Manual: Start worker, create incidents via incident-service
python3 -m src.main

# Verify audit records in DynamoDB
aws dynamodb scan --table-name cloud-incident-timeline-dev-audit-logs

# Monitor logs
aws logs tail /cloud-incident-timeline-dev/audit-worker --follow
```

## Graceful Shutdown

Respects `SIGTERM` (ECS) and `SIGINT` (Ctrl+C):
- Stops accepting new messages
- Completes current message processing
- Exits cleanly

## Error Handling

| Scenario | Action |
|----------|--------|
| Invalid JSON | Delete (won't improve) |
| Malformed event | Delete (validation failed) |
| Duplicate event | Delete (idempotent) |
| DynamoDB/SQS error | Retry (leave in queue) |

Failed messages after 3 retries go to DLQ: `cloud-incident-timeline-dev-audit-dlq`

## Deployment

```bash
# Build & push Docker image
docker build -t audit-worker:0.1.0 services/audit-worker/
docker tag audit-worker:0.1.0 $ACCOUNT_ID.dkr.ecr.eu-west-3.amazonaws.com/cloud-incident-timeline-dev-audit-worker:0.1.0
docker push $ACCOUNT_ID.dkr.ecr.eu-west-3.amazonaws.com/cloud-incident-timeline-dev-audit-worker:0.1.0
```

ECS Task Definition: 256 CPU, 512 MB memory, desired_count=1 (no load balancer).

## Troubleshooting

**Worker not processing:**
```bash
aws sqs get-queue-attributes --queue-url $AUDIT_QUEUE_URL --attribute-names All
aws logs tail /cloud-incident-timeline-dev/audit-worker --follow
```

**DynamoDB write fails:**
```bash
aws dynamodb describe-table --table-name cloud-incident-timeline-dev-audit-logs
```

**High backlog:**
Increase `desired_count` (2-3 workers) for parallel processing.

## References

- [Architecture](../../docs/ARCHITECTURE.md)
- [Deployment Guide](../../docs/DEPLOYMENT.md)
- [Data & Events Spec](../../.github/specs/06-data-and-events.md)
