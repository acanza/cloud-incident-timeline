# Development Environment

## Purpose

The `environments/dev/` layer composes all Terraform modules to create a complete development infrastructure for the cloud-incident-timeline project.

This is the **entry point** for `terraform plan` and `terraform apply`.

## Structure

```
environments/dev/
├── versions.tf          (Terraform + provider versions)
├── providers.tf         (AWS provider configuration)
├── variables.tf         (Environment variables)
├── terraform.tfvars     (Default values)
├── main.tf              (Module composition + service definitions)
├── outputs.tf           (Output values for accessing infrastructure)
└── README.md            (This file)
```

## Module Composition & Implementation Phases

### Phase 1: Infrastructure Skeleton ✅
- **networking**: VPC (10.20.0.0/16), public subnets, Internet Gateway, security groups
- **ecr**: ECR repositories for incident-service, timeline-service, audit-worker
- **ecs_cluster**: ECS Fargate cluster
- **alb**: Application Load Balancer on port 80 with health checks

### Phase 2: HTTP Services ✅
- **incident_service**: HTTP service on port 3000, connected to ALB via `/incidents*` target group
- **timeline_service**: HTTP service on port 3000, connected to ALB via `/incidents/*/timeline*` target group
- **iam**: Shared task execution role + service-specific task roles

### Phase 3: Data Layer ✅
- **dynamodb**: Three DynamoDB tables (on-demand billing):
  - `incidents` — incident records (PK: incident_id)
  - `incident_timeline` — timeline events (PK: incident_id, SK: created_at)
  - `audit_logs` — audit records (PK: entity_id, SK: created_at)
- **iam**: Service-specific permissions:
  - `incident-service` → access to `incidents` table
  - `timeline-service` → access to `incident_timeline` table
  - `audit-worker` → access to `audit_logs` table

### Phase 4: Async Architecture ✅
- **sqs**: Audit queue with dead-letter queue (max_receive_count = 3)
- **eventbridge**: Custom event bus + rule to route incidents events to SQS
- **audit_worker**: Async worker service that consumes SQS messages and writes to audit_logs
- **iam**: Permissions for:
  - EventBridge → send messages to SQS
  - audit-worker → consume from SQS and write to audit_logs

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `eu-west-3` | AWS region |
| `project_name` | `cloud-incident-timeline` | Project name |
| `environment` | `dev` | Environment name |
| `vpc_cidr` | `10.20.0.0/16` | VPC CIDR block |
| `public_subnet_cidrs` | `["10.20.1.0/24", "10.20.2.0/24"]` | Public subnet ranges |
| `container_port` | `3000` | Container port for HTTP services |
| `log_retention_days` | `3` | CloudWatch Logs retention |
| `service_cpu` | `{incident-service: 256, timeline-service: 256, audit-worker: 256}` | Task CPU units |
| `service_memory` | `{incident-service: 512, timeline-service: 512, audit-worker: 512}` | Task memory (MB) |
| `service_desired_count` | `{incident-service: 1, timeline-service: 1, audit-worker: 1}` | Desired task count |

## Deployment

### Initialize
```bash
cd infrastructure/environments/dev
terraform init
```

### Validate
```bash
terraform validate
```

### Plan
```bash
terraform plan -out=tfplan
```

### Apply
```bash
terraform apply tfplan
```

### Destroy
```bash
terraform destroy
```

## Key Outputs

After deployment, use these outputs to access the infrastructure:

- **ALB DNS Name**: `alb_dns_name` — Use to access services
- **Incident Service URL**: `http://<ALB_DNS>/incidents`
- **Timeline Service URL**: `http://<ALB_DNS>/incidents/{incidentId}/timeline`
- **EventBridge Bus**: `eventbridge_event_bus_name` — Used by incident-service to publish events
- **Audit Queue**: `audit_queue_url` — Monitored by audit-worker
- **DynamoDB Tables**: `dynamodb_table_names` — See all table names

## Design Decisions

### Decoupling Pattern
- The `ecs-service` module is independent of the ALB
- HTTP services connect to ALB via optional `target_group_arn` parameter
- Worker services (audit-worker) run without any ALB involvement
- All services use the same module and task role attachment pattern

### Network Architecture
- All tasks run in **public subnets** with public IPs
- No NAT Gateway (out of scope for v0.1)
- ALB security group allows inbound HTTP (0.0.0.0/0)
- ECS security group allows inbound only from ALB on container port

### State Management
- Uses **local Terraform state** (`.terraform/terraform.tfstate`)
- No remote backend (out of scope for v0.1)

### Cost Optimization
- On-demand DynamoDB billing (no provisioned throughput)
- CloudWatch Logs retention: 3 days only
- Minimal task CPU/memory (256 CPU, 512 MB memory)
- Forces deletion enabled on ECR for easy cleanup

## Cleanup

To destroy all infrastructure:
```bash
terraform destroy
```

This removes all resources including:
- VPC and networking
- ECS services and task definitions
- ALB and target groups
- DynamoDB tables
- ECR repositories (with forced deletion)
- EventBridge bus and rules
- SQS queues
- IAM roles and policies
- CloudWatch Log Groups

| `aws_region` | `eu-west-3` | AWS region |
| `project_name` | `cloud-incident-timeline` | Project name |
| `environment` | `dev` | Environment name |
| `vpc_cidr` | `10.20.0.0/16` | VPC CIDR |
| `public_subnet_cidrs` | `["10.20.1.0/24", "10.20.2.0/24"]` | Public subnet CIDRs |
| `service_cpu` | `{incident: 256, timeline: 256, audit: 256}` | CPU per service |
| `service_memory` | `{incident: 512, timeline: 512, audit: 512}` | Memory per service |
| `service_desired_count` | `{incident: 1, timeline: 1, audit: 1}` | Task count per service |
| `container_port` | `3000` | Container port for HTTP services |
| `log_retention_days` | `3` | CloudWatch log retention |

## Outputs

Key outputs for accessing infrastructure:

| Output | Description |
|--------|-------------|
| `alb_dns_name` | DNS name of the ALB (use to access services) |
| `ecr_repository_urls` | ECR image URLs for pushing Docker images |
| `ecs_cluster_name` | ECS cluster name |
| `access_info` | Quick reference URLs for services |

## Usage

### Initialize Terraform

```bash
cd infrastructure/environments/dev
terraform init
```

### Validate Configuration

```bash
terraform validate
terraform fmt
```

### Plan Deployment

```bash
terraform plan
```

### Deploy Infrastructure

```bash
terraform apply
```

### Destroy Infrastructure

```bash
terraform destroy
```

## Prerequisites

Before running Terraform:

1. **AWS Credentials** configured locally
2. **Docker images built and pushed to ECR**
   ```bash
   # Build and push incident-service
   aws ecr get-login-password --region eu-west-3 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.eu-west-3.amazonaws.com
   docker build -t cloud-incident-timeline-dev-incident-service:dev services/incident-service/
   docker tag cloud-incident-timeline-dev-incident-service:dev <account_id>.dkr.ecr.eu-west-3.amazonaws.com/cloud-incident-timeline-dev-incident-service:dev
   docker push <account_id>.dkr.ecr.eu-west-3.amazonaws.com/cloud-incident-timeline-dev-incident-service:dev
   
   # Repeat for timeline-service and audit-worker
   ```

## Architecture Overview

```
Internet
  ↓ (HTTP 80)
ALB (cloud-incident-timeline-dev-alb)
  ├─ Path: /incidents* → incident-service target group
  └─ Path: /incidents/*/timeline* → timeline-service target group
      ↓
  ECS Cluster (cloud-incident-timeline-dev-cluster)
      ├─ incident-service (Fargate task)
      │   └─ Container port 3000
      │       └─ IAM: DynamoDB incidents + EventBridge
      │
      ├─ timeline-service (Fargate task)
      │   └─ Container port 3000
      │       └─ IAM: DynamoDB timeline
      │
      └─ audit-worker (not on ALB, scheduled for Phase 4)
          └─ Container port 9000
              └─ IAM: SQS + DynamoDB audit_logs
```

## Accessing Services

After `terraform apply`, use the ALB DNS name to access services:

```bash
# Get ALB DNS name
terraform output alb_dns_name

# Example URLs
curl http://cloud-incident-timeline-dev-alb-1234567890.eu-west-3.elb.amazonaws.com/health
curl http://cloud-incident-timeline-dev-alb-1234567890.eu-west-3.elb.amazonaws.com/incidents
curl http://cloud-incident-timeline-dev-alb-1234567890.eu-west-3.elb.amazonaws.com/incidents/inc-123/timeline
```

## Health Checks

ALB health checks are configured for both services on the `/health` endpoint:
- **Path**: `/health`
- **Expected Response**: HTTP 200 with JSON `{"status": "ok", "service": "..."}`
- **Interval**: 30 seconds
- **Healthy Threshold**: 2 consecutive passes
- **Unhealthy Threshold**: 2 consecutive failures

## Logs

CloudWatch Logs are organized by service:

```
/ecs/incident-service
/ecs/timeline-service
/ecs/audit-worker
```

To view logs:

```bash
aws logs tail /ecs/incident-service --follow
```

## Cost Considerations

- **Fargate**: Per-task per-second pricing
- **ALB**: Per-hour + data processing
- **CloudWatch**: Logs ingestion + retention
- **DynamoDB**: On-demand pricing (v0.1, not autoscaling)
- **ECR**: Per-stored image (images from docker push)

Estimated monthly cost for v0.1 (1 task per service, 3-day log retention): ~$5-10 USD

## Common Issues

### Services not healthy

1. Ensure Docker images are pushed to ECR with correct tag (`dev`)
2. Check security groups allow traffic from ALB
3. Verify container health check endpoint responds with HTTP 200
4. Check CloudWatch logs for container errors

### ALB target group shows unhealthy

1. Check ECS service task definition is using correct image URL
2. Verify container is listening on port 3000
3. Check `/health` endpoint returns HTTP 200
4. Review CloudWatch logs for errors

### Cannot connect to ALB

1. Ensure ALB security group allows HTTP 80 from 0.0.0.0/0
2. Verify subnets are public (have route to IGW)
3. Check ALB is in "active" state (not provisioning)
