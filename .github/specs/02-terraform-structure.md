# Cloud Incident Timeline — Terraform Structure Specification

## Expected repository structure

The infrastructure code must be located under:

```text
infrastructure/
```

Recommended structure:

```text
infrastructure/
├── environments/
│   └── dev/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── providers.tf
│       ├── versions.tf
│       └── terraform.tfvars
│
└── modules/
    ├── networking/
    ├── alb/
    ├── ecr/
    ├── ecs-cluster/
    ├── ecs-service/
    ├── dynamodb/
    ├── eventbridge/
    └── sqs/
```

## Environment layer

The `environments/dev` layer is responsible for composing the modules.

It should contain minimal resource definitions directly. Most resources should be created through modules.

The environment layer should define:

* Provider configuration.
* Common locals.
* Module calls.
* Environment-specific variables.
* Outputs useful for testing.

## Required modules

### networking

Responsible for:

* VPC.
* Public subnets.
* Internet Gateway.
* Public route table.
* Route table associations.
* Security group for the ALB.
* Security group for ECS services.

The first version must not create:

* NAT Gateway.
* Private subnets.
* VPC endpoints.

### alb

Responsible for:

* Application Load Balancer.
* HTTP listener.
* Target groups (defined but not wired to services by this module).
* Listener rules.
* Health check configuration.

**Important — Decoupling**:
- The ALB module creates target group definitions only
- The `ecs-service` module is NOT a dependency of the ALB module
- The environment layer is responsible for attaching services to target groups
- This allows worker services to exist without any ALB involvement

The first version should use HTTP on port `80`.

HTTPS, ACM and Route 53 are out of scope for v0.1.

### ecr

Responsible for:

* Creating one ECR repository per service.
* Enabling forced deletion for development usage.

Required repositories:

* `incident-service`
* `timeline-service`
* `audit-worker`

### ecs-cluster

Responsible for:

* ECS cluster.
* Optional cluster-level settings.

The first version should keep this module simple.

### ecs-service

**Decoupled, reusable module for ECS Fargate services** — designed to be independent of the ALB.

The module manages the full lifecycle of an ECS service without direct knowledge of load balancers or target groups. Services can optionally receive traffic through target groups created and managed separately.

#### Service Types Supported

1. **HTTP Services** (e.g., `incident-service`, `timeline-service`)
   - No hardcoded target group dependency in the module
   - Service can be attached to a target group via optional input variable
   - Target group management remains in the `alb` module
   - Decoupling: The environment layer composes the service + ALB modules together

2. **Asynchronous Worker Services** (e.g., `audit-worker`)
   - No target group attachment
   - No public IP assignment (typically)
   - Processes messages from SQS or events from EventBridge
   - Container can pull messages independently

#### Module Inputs

* `service_name` — Name of the service.
* `cluster_name` — ECS cluster name.
* `container_image` — Docker image URI (e.g., ECR repository URL with tag).
* `container_port` — Port the container listens on (required, but may not be exposed publicly).
* `cpu` — Task CPU units (e.g., 256, 512, 1024).
* `memory` — Task memory in MB (e.g., 512, 1024, 2048).
* `desired_count` — Number of desired task instances.
* `environment_variables` — Map of container environment variables.
* `task_execution_role_arn` — IAM role ARN for task execution (ECR pull, CloudWatch Logs).
* `task_role_arn` — IAM role ARN for task permissions (SQS, DynamoDB, etc.).
* `log_group_name` — CloudWatch Log Group name.
* `log_retention_days` — Log retention period.
* `security_group_ids` — Security groups for the service (from `networking` module).
* `subnet_ids` — Subnets for task placement.
* **Optional**: `target_group_arn` — Target group ARN for HTTP services (defaults to `null`).
* **Optional**: `assign_public_ip` — Boolean to assign public IPs (defaults to `false`).

#### Module Outputs

* `service_arn` — ARN of the created ECS service.
* `service_name` — Name of the ECS service.
* `task_definition_arn` — ARN of the task definition.
* `log_group_name` — CloudWatch Log Group name.

#### Decoupling Pattern

**How the environment layer composes HTTP services with the ALB**:

```hcl
# In environments/dev/main.tf

module "incident_service" {
  source = "../../modules/ecs-service"
  
  service_name           = "incident-service"
  cluster_name           = module.ecs_cluster.cluster_name
  container_image        = "${module.ecr.incident_service_repository_url}:latest"
  container_port         = 8080
  # ... other required inputs
  
  # Service does NOT know about the ALB directly
  target_group_arn       = module.alb.incident_target_group_arn  # Passed from ALB module
}

module "audit_worker" {
  source = "../../modules/ecs-service"
  
  service_name           = "audit-worker"
  cluster_name           = module.ecs_cluster.cluster_name
  container_image        = "${module.ecr.audit_worker_repository_url}:latest"
  container_port         = 9000  # Worker service, not exposed externally
  # ... other required inputs
  
  # NO target_group_arn for worker services
  target_group_arn       = null
}
```

This design ensures:
- The `ecs-service` module has zero dependencies on the `alb` module
- Worker services and HTTP services use the identical module
- The environment layer is responsible for wiring target groups to services
- Services remain independently testable and portable

### dynamodb

Responsible for creating DynamoDB tables.

Required tables:

* `incidents`
* `incident_timeline`
* `audit_logs`

Billing mode should be:

```hcl
billing_mode = "PAY_PER_REQUEST"
```

### eventbridge

Responsible for:

* Custom EventBridge bus.
* EventBridge rules.
* EventBridge targets.
* IAM permissions required to send events to SQS.

### sqs

Responsible for:

* Audit queue.
* Optional dead-letter queue.

For v0.1, a DLQ is recommended but not mandatory.

## Terraform standards

The Terraform code should follow these standards:

* Use clear variable names.
* Use `locals` for repeated naming patterns.
* Use tags consistently.
* Avoid hardcoded project names inside modules.
* Prefer reusable modules over copy-pasted resources.
* Keep modules small and focused.
* Expose only useful outputs.
* Avoid unnecessary abstractions.

### Module Composition in the Environment Layer

The environment layer (`environments/dev`) is responsible for composing independent modules.

**Key decoupling principle**: Modules should not have hard dependencies on each other. Instead, the environment layer passes outputs between modules.

Example composition pattern:

```hcl
# environments/dev/main.tf

# Networking is foundational - others depend on it
module "networking" {
  source = "../../modules/networking"
  # ...
}

# ALB is independent (depends only on networking)
module "alb" {
  source = "../../modules/alb"
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
  # ...
}

# ECS cluster is independent
module "ecs_cluster" {
  source = "../../modules/ecs-cluster"
  # ...
}

# ECR is independent
module "ecr" {
  source = "../../modules/ecr"
  # ...
}

# Services depend on: networking, ecs-cluster, ecr
# Services are OPTIONALLY connected to ALB target groups by the environment layer
module "incident_service" {
  source = "../../modules/ecs-service"
  
  cluster_name           = module.ecs_cluster.cluster_name
  security_group_ids     = [module.networking.ecs_security_group_id]
  subnet_ids             = module.networking.public_subnet_ids
  container_image        = "${module.ecr.incident_service_repository_url}:latest"
  
  # OPTIONAL: Connect to ALB (passed from ALB module, but service doesn't depend on ALB module)
  target_group_arn       = module.alb.incident_target_group_arn
  # ...
}

module "audit_worker" {
  source = "../../modules/ecs-service"
  
  cluster_name           = module.ecs_cluster.cluster_name
  security_group_ids     = [module.networking.ecs_security_group_id]
  subnet_ids             = module.networking.public_subnet_ids
  container_image        = "${module.ecr.audit_worker_repository_url}:latest"
  
  # NO ALB connection - this is a pure worker service
  target_group_arn       = null
  # ...
}

# EventBridge, SQS, DynamoDB are independent
# They are wired to services via environment variables or IAM permissions
```

This composition approach enables:
- Worker services without any HTTP/ALB infrastructure
- Easy addition of new worker services in the future
- Independent module testing
- Clear separation of concerns

## Required Terraform Defaults

The dev environment must define these defaults:

```hcl
project_name = "cloud-incident-timeline"
environment  = "dev"
aws_region   = "eu-west-3"

vpc_cidr = "10.20.0.0/16"

public_subnet_cidrs = [
  "10.20.1.0/24",
  "10.20.2.0/24"
]

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

service_desired_count = {
  incident-service = 1
  timeline-service = 1
  audit-worker     = 1
}

container_port = 3000

image_tag = "dev"

log_retention_in_days = 3

enable_remote_state = false
enable_nat_gateway  = false
enable_https        = false
enable_cognito      = false
enable_autoscaling  = false
```

The first version must use local Terraform state.

Terraform version constraint:

```hcl
required_version = ">= 1.6.0, < 2.0.0"
```

AWS provider constraint:

```hcl
required_providers {
  aws = {
    source  = "hashicorp/aws"
    version = "~> 5.0"
  }
}
```

## Outputs

The dev environment should output at least:

* ALB DNS name.
* ECS cluster name.
* ECR repository URLs.
* DynamoDB table names.
* EventBridge bus name.
* SQS queue URL.

## Destroy safety

The infrastructure must be designed to support frequent destruction with:

```bash
terraform destroy
```

Avoid resources that block deletion.

Specific requirements:

* ECR repositories should allow forced deletion.
* No deletion protection on ALB.
* No deletion protection on DynamoDB tables.
* CloudWatch Log Groups should have short retention.
* S3 buckets are out of scope for v0.1 unless explicitly requested.
