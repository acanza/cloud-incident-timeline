# Cloud Incident Timeline — Project Context

## Project name

`cloud-incident-timeline`

## Goal

This project is a small-scale portfolio project designed to practice microservices architecture on AWS using ECS Fargate, Application Load Balancer, ECR, DynamoDB, EventBridge, SQS, CloudWatch Logs and Terraform.

The main objective is not to build a production-grade incident management platform, but to implement a realistic and understandable AWS microservices architecture at small scale.

## Main learning goals

The infrastructure must help demonstrate the following concepts:

* Containerized microservices on ECS Fargate.
* Docker images stored in Amazon ECR.
* Public Application Load Balancer with path-based routing.
* Multiple ECS services deployed into a single ECS cluster.
* Independent target groups per HTTP service.
* Task definitions with service-specific environment variables.
* IAM execution roles and task roles.
* DynamoDB tables owned by individual services.
* Asynchronous communication using EventBridge and SQS.
* Worker service running as an ECS Fargate task.
* CloudWatch Logs for container logs.
* Terraform modules and reusable infrastructure patterns.
* Cost-aware infrastructure that can be created and destroyed frequently.

## Scope of the first version

The first version must be small enough to implement in approximately 30 hours.

The first version includes:

* One VPC.
* Two public subnets in different Availability Zones.
* One Internet Gateway.
* One public Application Load Balancer.
* One ECS cluster.
* Three ECR repositories.
* Three ECS Fargate services:

  * `incident-service`
  * `timeline-service`
  * `audit-worker`
* Two HTTP services exposed through the ALB:

  * `incident-service`
  * `timeline-service`
* One asynchronous worker:

  * `audit-worker`
* Three DynamoDB tables:

  * `incidents`
  * `incident_timeline`
  * `audit_logs`
* One EventBridge custom event bus.
* One SQS queue for audit events.
* CloudWatch Log Groups for all ECS services.
* IAM roles with least-privilege permissions where practical.
* Terraform outputs with the ALB DNS name and relevant resource names.

## Explicitly out of scope for v0.1

The following features must not be implemented in the first version unless explicitly requested later:

* NAT Gateway.
* Private subnets for ECS tasks.
* Route 53.
* ACM certificates.
* HTTPS listener.
* Custom domain.
* Cognito authentication.
* Frontend deployment.
* API Gateway.
* Lambda.
* Bedrock.
* SES notifications.
* Slack integration.
* GitHub integration.
* Multi-environment setup beyond `dev`.
* Autoscaling policies.
* Blue/green deployments.
* Service discovery.
* X-Ray tracing.
* Production-grade multi-AZ high availability.

## Cost-control principle

This project is intended to be deployed temporarily for testing and then destroyed using:

```bash
terraform destroy
```

Resources should be designed to avoid destroy failures where possible.

Examples:

* ECR repositories should support forced deletion.
* Log groups should have short retention.
* No deletion protection should be enabled.
* No NAT Gateway should be created in v0.1.
* ECS desired count should default to `1`.
* CPU and memory values should be minimal.

## Recommended AWS region

Default region:

```text
eu-west-3
```

## Naming convention

All resources should use the following naming pattern where possible:

```text
${project_name}-${environment}-${resource_name}
```

Default values:

```hcl
project_name = "cloud-incident-timeline"
environment  = "dev"
```

Example:

```text
cloud-incident-timeline-dev-alb
cloud-incident-timeline-dev-cluster
cloud-incident-timeline-dev-incidents
cloud-incident-timeline-dev-incident-service
```
