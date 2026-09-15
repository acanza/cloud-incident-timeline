# Cloud Incident Timeline

A hands-on learning project that builds a real-world incident management system using **decoupled microservices** that communicate asynchronously through **event-driven architecture**. Learn how to design scalable, resilient systems on AWS using **Terraform for Infrastructure as Code**, modern messaging patterns with EventBridge and SQS, and containerized services with ECS Fargate.

## Quick Start

```bash
# 1. Set up infrastructure
cd infrastructure/environments/dev
terraform init
terraform plan
terraform apply

# 2. Deploy services (see deployment guide)
# 3. Test endpoints (see service README files)
```

## End-to-End Test

After deploying all services, validate that the complete system works correctly with the automated end-to-end test.

### Prerequisites

```bash
# Ensure you have AWS credentials configured
aws sts get-caller-identity

# Install Python dependencies
pip install requests boto3
```

### Running the Test

```bash
# From the project root directory
python3 test-e2e-flow.py
```

### Test Execution Flow

The test validates the complete incident lifecycle across all services:

1. **Health Checks** ✓
   - Verifies incident-service responds at `GET /incidents/health`
   - Verifies timeline-service responds at `GET /incidents/health/timeline/health`

2. **Incident Creation** ✓
   - Creates a new incident via `POST /incidents` 
   - Validates HTTP 201 response with incident_id
   - Publishes `IncidentCreated` event to EventBridge

3. **DynamoDB Incidents Table** ✓
   - Queries the incidents table by incident_id
   - Validates incident persists with correct fields:
     - `title`, `description`, `severity`, `status`
     - `created_at` timestamp
   - Confirms data is immediately available (DynamoDB eventual consistency)

4. **DynamoDB Timeline Table** ✓
   - Queries incident-timeline table for the created incident
   - Validates `IncidentCreated` event is recorded with:
     - `incident_id` (hash key)
     - `created_at` (sort key)
     - Event metadata and data payload

5. **DynamoDB Audit-Logs Table** ✓
   - Queries audit-logs table by entity_id
   - Confirms audit-worker consumed SQS message successfully
   - Validates audit record contains:
     - `audit_id`, `entity_id`, `event_type`
     - `correlation_id` linking to incident
     - `created_at` timestamp

### Expected Output

Successful test execution will display:

```
================================================================================
TEST SUMMARY
================================================================================
Incidents Table:   ✓ PASS
Timeline Table:    ✓ PASS
Audit Logs Table:  ✓ PASS

Test Incident ID: inc-xxxxxxxxxxxxxxx
✓✓✓ END-TO-END TEST PASSED ✓✓✓
All critical components working correctly!
```

### What Gets Validated

| Component | Validation | Expected Result |
|-----------|-----------|-----------------|
| Health Checks | Both services respond 200 OK | ✅ Healthy |
| Incident API | Create incident, get 201 response | ✅ Created |
| EventBridge | Event published successfully | ✅ Published |
| SQS Queue | Messages routed from EventBridge | ✅ Routed |
| Audit-Worker | SQS messages consumed from audit queue | ✅ Consumed |
| Incidents Table | Incident persisted immediately | ✅ Persisted |
| Timeline Table | Event record created for incident | ✅ Recorded |
| Audit-Logs Table | Audit record created from event | ✅ Logged |

### Troubleshooting

If tests fail:

```bash
# Check service health directly
curl http://ALB_URL/incidents/health
curl http://ALB_URL/incidents/health/timeline/health

# View service logs (replace with your ALB URL and service name)
aws logs tail /ecs/incident-service --follow --region eu-west-3
aws logs tail /ecs/audit-worker --follow --region eu-west-3

# Inspect DynamoDB tables
aws dynamodb scan --table-name cloud-incident-timeline-dev-incidents --region eu-west-3

# Check SQS queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.eu-west-3.amazonaws.com/YOUR_ACCOUNT_ID/audit-queue \
  --attribute-names All \
  --region eu-west-3
```

## Tech Stack

- **Services**: Python 3.11, FastAPI
- **Container Runtime**: ECS Fargate
- **Data**: DynamoDB (NoSQL)
- **Messaging**: EventBridge, SQS
- **API Gateway**: Application Load Balancer (ALB)
- **Infrastructure**: Terraform

## Architecture Diagram

![Cloud Incident Timeline Architecture](./docs/cloud-incident-timeline-diagram.png)

## Project Structure

```
.
├── infrastructure/          # Terraform modules & environments
│   ├── modules/            # Reusable AWS components
│   └── environments/dev/    # Dev environment configuration
├── services/               # Microservices
│   ├── incident-service/   # HTTP API for incident management
│   ├── timeline-service/   # HTTP API for incident timeline
│   └── audit-worker/       # Async worker for audit logs
└── .github/specs/          # Architecture & implementation specs
```

## Cost Estimation

This project is designed for **minimal cost** using AWS Free Tier services. Estimated daily cost with light testing:

| Service | Configuration | Daily Cost |
|---------|---------------|-----------|
| **ECS Fargate** | 3 tasks × 256 CPU (0.5 GB) | ~$1-2 |
| **DynamoDB** | On-demand pricing, 3 tables | ~$0-1 |
| **Application Load Balancer** | Fixed hourly charge | ~$0.50 |
| **CloudWatch Logs** | 3-day retention, minimal volume | ~$0.10 |
| **Data Transfer** | Internal AWS communication | ~$0 |
| **EventBridge + SQS** | Minimal volume, within free tier | ~$0 |
| | **Total Estimated Daily Cost** | **~$2-5** |

**Cost-Control Strategies:**
- ✅ No NAT Gateway (saves ~$32/month)
- ✅ No autoscaling (predictable, fixed cost)
- ✅ Public subnets only (minimal data transfer)
- ✅ Destroy after testing (pay only during active use)

## Documentation

### Getting Started
- [**Architecture**](./docs/ARCHITECTURE.md) — Complete system design with diagrams
- [**Deployment Guide**](./docs/DEPLOYMENT.md) — Prerequisites, setup, validation
- [**Destroy Guide**](./docs/DESTROY.md) — Safe cleanup, backup strategy

### Service Documentation
- [incident-service](./services/incident-service/README.md) — REST API for incident CRUD
- [timeline-service](./services/timeline-service/README.md) — Timeline queries & comments
- [audit-worker](./services/audit-worker/README.md) — Event processing & audit logs

### Comprehensive Checklist
- [**Phase 5: Documentation Completion**](./docs/PHASE_5_COMPLETION.md) — All documentation verified & complete

### Specifications (Deep Dive)
- [Project Context](./github/specs/00-project-context.md)
- [Architecture Spec](./github/specs/01-architecture.md)
- [Data & Events](./github/specs/06-data-and-events.md)
- [Cost Control](./github/specs/07-cost-control.md)
