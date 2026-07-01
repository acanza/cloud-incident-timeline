# Security and IAM Specification

## Security principles

Apply least privilege where practical.

The first version is a learning project, but IAM permissions should still be service-specific.

## ECS task execution role

The ECS task execution role should allow ECS to:

- Pull images from ECR.
- Write logs to CloudWatch Logs.

## ECS task roles

Each service should have its own task role.

### incident-service permissions

Allow:

- Read/write access to the `incidents` DynamoDB table.
- `events:PutEvents` on the project EventBridge bus.

Do not allow:

- Access to `incident_timeline`.
- Access to `audit_logs`.
- Access to SQS unless required later.

### timeline-service permissions

Allow:

- Read/write access to the `incident_timeline` DynamoDB table.

Do not allow:

- Access to `incidents`.
- Access to `audit_logs`.
- EventBridge publish permissions unless required later.

### audit-worker permissions

Allow:

- Receive/delete messages from the audit SQS queue.
- Write access to the `audit_logs` DynamoDB table.

Do not allow:

- Public HTTP access.
- EventBridge publish permissions unless required later.
- Access to unrelated DynamoDB tables.

## Public access

The only public entry point should be the ALB.

ECS tasks must not allow direct inbound traffic from the internet.

## Secrets

No Secrets Manager integration is required in v0.1.

Do not hardcode secrets in Terraform variables, Dockerfiles or application code.