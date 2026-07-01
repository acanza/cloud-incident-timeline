# ECS Fargate Specification

## Cluster

Create one ECS cluster for the dev environment.

## Services

Create three ECS services:

- `incident-service`
- `timeline-service`
- `audit-worker`

## Launch type

Use Fargate.

## CPU and memory

Default values:

```hcl
cpu    = 256
memory = 512
```
## Desire count

```hcl
desired_count = 1
```

## Deployment

Use rolling deployment defaults unless there is a specific reason to customize them.

## Containers

Each service must have its own Docker image stored in ECR.

Each container must send logs to CloudWatch Logs.

## Ports

HTTP services should expose container port 3000 unless the application defines another port.

The audit worker does not need a load balancer or exposed port.

## Health checks

HTTP services must expose:
GET /health

The ALB target groups must use this endpoint.

### Environment variables

Each service should receive only the environment variables it needs.

Examples:

### incident-service
AWS_REGION
INCIDENTS_TABLE_NAME
EVENT_BUS_NAME

### timeline-service
AWS_REGION
TIMELINE_TABLE_NAME

### audit-worker
AWS_REGION
AUDIT_TABLE_NAME
AUDIT_QUEUE_URL

## IAM

Each task must use a task role with least-privilege permissions.

Do not reuse one broad task role for all services unless temporarily needed during development.