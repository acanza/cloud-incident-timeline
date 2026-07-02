# Implementation Decisions

## 1. Docker Images

### Dockerfiles

For v0.1, Dockerfiles must be created inside each service directory.

Required service directories:

```text
services/
├── incident-service/
│   ├── Dockerfile
│   └── src/
├── timeline-service/
│   ├── Dockerfile
│   └── src/
└── audit-worker/
    ├── Dockerfile
    └── src/
```

The infrastructure must create the ECR repositories, but the Docker images are built and pushed separately before running the ECS services successfully.

Terraform must not build Docker images.

### ECR repositories

Terraform must create one ECR repository per service:

```text
incident-service
timeline-service
audit-worker
```

Repository names must follow the project naming convention:

```text
${project_name}-${environment}-${service_name}
```

Example:

```text
cloud-incident-timeline-dev-incident-service
cloud-incident-timeline-dev-timeline-service
cloud-incident-timeline-dev-audit-worker
```

### Image tag strategy

For v0.1, use a simple development tag:

```text
dev
```

Do not use `latest` as the default image tag.

Reason:

* `latest` is ambiguous.
* `dev` makes the environment intent explicit.
* More advanced immutable tags can be introduced later through CI/CD.

Default image URI pattern:

```text
<account_id>.dkr.ecr.<aws_region>.amazonaws.com/<repository_name>:dev
```

The `ecs-service` module must receive the full image URI as an input variable.

Example:

```hcl
container_image = "${module.ecr.repository_urls["incident-service"]}:dev"
```

### Future improvement

In a later CI/CD phase, the image tag can be changed to an immutable value such as:

```text
git-sha
```

Example:

```text
cloud-incident-timeline-dev-incident-service:a1b2c3d
```

For v0.1, this is out of scope.

---

## 2. Terraform Variables

### AWS region

Default region:

```hcl
aws_region = "eu-west-3"
```

### Project name

Default:

```hcl
project_name = "cloud-incident-timeline"
```

### Environment

Default:

```hcl
environment = "dev"
```

### VPC CIDR

Use the following default CIDR block:

```hcl
vpc_cidr = "10.20.0.0/16"
```

Reason:

* It avoids the very common `10.0.0.0/16` range.
* It is still simple and readable.
* It is enough for a small portfolio project.

### Public subnet CIDRs

Use two public subnets across two Availability Zones:

```hcl
public_subnet_cidrs = [
  "10.20.1.0/24",
  "10.20.2.0/24"
]
```

The environment should automatically select the first two available Availability Zones in the selected region unless explicitly overridden.

### Private subnets

Private subnets are out of scope for v0.1.

Do not create:

* Private subnets.
* NAT Gateway.
* Private route tables.
* VPC endpoints.

### ECS CPU and memory

CPU and memory must be configurable per service, but defaults should be minimal.

Default values:

```hcl
service_cpu = {
  incident-service = 256
  timeline-service = 256
  audit-worker     = 256
}

service_memory = {
  incident-service = 512
  timeline-service = 512
  audit-worker     = 512
}
```

Reason:

* All services start with the smallest practical Fargate shape.
* Per-service configuration makes future tuning easier.
* The interface is clearer than one global value if services evolve differently.

### ECS desired count

Use desired count per service.

Default:

```hcl
service_desired_count = {
  incident-service = 1
  timeline-service = 1
  audit-worker     = 1
}
```

For v0.1, do not configure autoscaling.

### Container port

HTTP services should expose:

```hcl
container_port = 3000
```

The audit worker does not need a public container port and must not be attached to an ALB target group.

### CloudWatch log retention

Use short retention:

```hcl
log_retention_in_days = 3
```

### Terraform state

For v0.1, use local Terraform state.

Remote state is out of scope for the first version.

Reason:

* This is a personal portfolio project.
* The infrastructure will be deployed temporarily and destroyed frequently.
* Remote state adds extra resources, configuration and lifecycle concerns.

Do not create in v0.1:

* S3 backend bucket.
* DynamoDB state lock table.
* Remote backend bootstrap module.

A future version may introduce remote state using:

```text
S3 backend + DynamoDB locking
```

### Terraform version

Use the following Terraform constraint:

```hcl
required_version = ">= 1.6.0, < 2.0.0"
```

Reason:

* Avoids very old Terraform versions.
* Keeps compatibility broad.
* Prevents accidental upgrade to a future major version.

### AWS provider version

Use the following provider constraint:

```hcl
required_providers {
  aws = {
    source  = "hashicorp/aws"
    version = "~> 5.0"
  }
}
```

Reason:

* AWS provider v5 is mature and widely used.
* Avoids automatic breaking changes from a future major version.

---

## 3. EventBridge Event Bus

### Custom event bus name

Use a custom EventBridge bus.

Name pattern:

```text
${project_name}-${environment}-event-bus
```

Default resolved name:

```text
cloud-incident-timeline-dev-event-bus
```

### Event source

Use this event source for events published by the incident service:

```text
cloud-incident-timeline.incident-service
```

### Required event types

The first version must support these event types:

```text
IncidentCreated
IncidentStatusChanged
```

### EventBridge rule for audit events

Create one EventBridge rule that matches incident events and routes them to SQS.

Rule name:

```text
${project_name}-${environment}-audit-events-rule
```

Default resolved name:

```text
cloud-incident-timeline-dev-audit-events-rule
```

Event pattern:

```json
{
  "source": ["cloud-incident-timeline.incident-service"],
  "detail-type": ["IncidentCreated", "IncidentStatusChanged"]
}
```

### Audit SQS queue

Queue name pattern:

```text
${project_name}-${environment}-audit-queue
```

Default resolved name:

```text
cloud-incident-timeline-dev-audit-queue
```

### Dead-letter queue

For v0.1, create a dead-letter queue for the audit SQS queue.

Reason:

* It is low-cost.
* It demonstrates production-aware async design.
* It helps debug failed worker processing.

DLQ name pattern:

```text
${project_name}-${environment}-audit-dlq
```

Default resolved name:

```text
cloud-incident-timeline-dev-audit-dlq
```

Recommended redrive policy:

```hcl
max_receive_count = 3
```

### EventBridge target DLQ

Do not configure a separate EventBridge target DLQ in v0.1.

Reason:

* The EventBridge target is SQS.
* SQS already has its own DLQ for failed worker processing.
* Adding an EventBridge target DLQ increases complexity for limited benefit in this MVP.

This can be revisited in a later hardening phase.

---

## 4. Resource Lifecycle Defaults

### ECR

ECR repositories must allow forced deletion:

```hcl
force_delete = true
```

### ALB

Deletion protection must be disabled:

```hcl
enable_deletion_protection = false
```

### DynamoDB

Deletion protection must be disabled.

Point-in-time recovery is optional but should be disabled in v0.1 to keep the MVP simple.

### ECS

Use:

```hcl
assign_public_ip = true
```

For ECS services in v0.1.

Reason:

* ECS tasks run in public subnets.
* NAT Gateway is intentionally avoided.
* Inbound access is still restricted by security groups.

### Security groups

The only public inbound access must be the ALB security group on HTTP port 80.

ECS tasks must only allow inbound traffic from the ALB security group on the application port.

No ECS task security group rule should allow inbound traffic directly from `0.0.0.0/0`.

---

## 5. v0.1 Explicit Non-Goals

Do not implement the following unless explicitly requested:

* Docker image build from Terraform.
* `latest` image tag as default.
* Remote Terraform state.
* NAT Gateway.
* Private subnets.
* VPC endpoints.
* HTTPS.
* ACM.
* Route 53.
* Cognito.
* Frontend hosting.
* ECS autoscaling.
* Blue/green deployment.
* Service discovery.
* Multiple environments.
* EventBridge archive/replay.
* EventBridge target DLQ.
