# Implementation Phases Specification

## Phase 1 — Infrastructure skeleton

Implement:

- VPC.
- Public subnets.
- Internet Gateway.
- Security groups.
- ALB.
- ECS cluster.
- ECR repositories.

Do not implement application-specific permissions yet unless needed.

## Phase 2 — ECS HTTP services

Implement:

- `incident-service` task definition.
- `incident-service` ECS service.
- `incident-service` target group.
- ALB listener rule for `/incidents*`.
- `timeline-service` task definition.
- `timeline-service` ECS service.
- `timeline-service` target group.
- ALB listener rule for `/incidents/*/timeline*`.

Validate:

- Both services pass ALB health checks.
- Routes are correctly forwarded.

## Phase 3 — Data layer

Implement:

- `incidents` DynamoDB table.
- `incident_timeline` DynamoDB table.
- `audit_logs` DynamoDB table.
- Service-specific IAM task role permissions.

Validate:

- `incident-service` can access only its table.
- `timeline-service` can access only its table.

## Phase 4 — Async architecture

Implement:

- EventBridge custom bus.
- SQS audit queue.
- EventBridge rule to route incident events to SQS.
- `audit-worker` task definition.
- `audit-worker` ECS service.
- IAM permissions for SQS and audit table.

Validate:

- `incident-service` publishes an event.
- EventBridge forwards it to SQS.
- `audit-worker` consumes the message.
- Audit record is stored in DynamoDB.

## Phase 5 — Documentation

Create or update:

- README.md.
- Architecture diagram.
- Deployment instructions.
- Destroy instructions.
- Cost-control notes.
- API contracts.
- Event contracts.