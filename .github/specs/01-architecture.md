# Cloud Incident Timeline — Architecture Specification

## Architecture style

The project must use a small-scale microservices architecture based on ECS Fargate.

The first version must use containerized services, not Lambda functions.

## High-level architecture

The infrastructure must follow this logical architecture:

```text
Internet
  ↓
Application Load Balancer
  ↓
ECS Fargate services
  ├── incident-service
  ├── timeline-service
  └── audit-worker
  ↓
DynamoDB
  ↓
EventBridge
  ↓
SQS
```

## Services

### incident-service

Type:

```text
HTTP service
```

Responsibilities:

* Create incidents.
* List incidents.
* Retrieve incident details.
* Update incident status.
* Publish domain events to EventBridge.

Expected routes:

```http
POST /incidents
GET /incidents
GET /incidents/{incidentId}
PATCH /incidents/{incidentId}
GET /health
```

AWS resources:

* ECS Fargate service.
* ECR repository.
* Target group.
* CloudWatch Log Group.
* IAM task role with permissions to access the `incidents` DynamoDB table and publish events to EventBridge.

### timeline-service

Type:

```text
HTTP service
```

Responsibilities:

* Add manual timeline events.
* List timeline events for an incident.

Expected routes:

```http
POST /incidents/{incidentId}/timeline
GET /incidents/{incidentId}/timeline
GET /health
```

AWS resources:

* ECS Fargate service.
* ECR repository.
* Target group.
* CloudWatch Log Group.
* IAM task role with permissions to access the `incident_timeline` DynamoDB table.

### audit-worker

Type:

```text
Asynchronous worker
```

Responsibilities:

* Poll audit events from SQS.
* Process audit events.
* Store audit records in DynamoDB.

AWS resources:

* ECS Fargate service.
* ECR repository.
* CloudWatch Log Group.
* IAM task role with permissions to consume messages from the audit SQS queue and write to the `audit_logs` DynamoDB table.

The audit worker must not be attached to the Application Load Balancer.

## Load balancing

The architecture must use one public Application Load Balancer.

The ALB must route traffic using path-based routing.

Required routing rules:

```text
/incidents/*/timeline*  → timeline-service target group
/incidents*             → incident-service target group
```

The more specific `/incidents/*/timeline*` rule must have higher priority than `/incidents*`.

## Health checks

Each HTTP service must expose a health check endpoint:

```http
GET /health
```

The ALB target groups must use `/health` as the health check path.

Expected health response:

```json
{
  "status": "ok",
  "service": "incident-service"
}
```

or:

```json
{
  "status": "ok",
  "service": "timeline-service"
}
```

## Networking model

For v0.1, ECS tasks must run in public subnets with public IP assignment enabled.

This is an intentional cost-control decision to avoid NAT Gateway.

Security groups must ensure that ECS tasks only accept inbound traffic from the ALB security group.

The ALB must be public.

## Asynchronous flow

When an incident is created or its status changes, `incident-service` must publish an event to EventBridge.

EventBridge must route the relevant event to SQS.

The `audit-worker` must consume the SQS message and persist an audit record in DynamoDB.

Expected flow:

```text
incident-service
  ↓ PutEvents
EventBridge custom bus
  ↓ rule
SQS audit queue
  ↓ ReceiveMessage
audit-worker
  ↓ PutItem
DynamoDB audit_logs
```

## Data ownership

Each service should own its own data store.

* `incident-service` owns the `incidents` table.
* `timeline-service` owns the `incident_timeline` table.
* `audit-worker` owns the `audit_logs` table.

Services should not directly write to another service's table unless explicitly required.
