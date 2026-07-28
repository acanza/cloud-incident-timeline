# ============================================================================
# PHASE 1: Infrastructure Skeleton (Networking, ECR, ECS Cluster, ALB)
# ============================================================================

# Networking module
module "networking" {
  source = "../../modules/networking"

  project_name        = var.project_name
  environment         = var.environment
  aws_region          = var.aws_region
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
}

# ECR repositories for all services
module "ecr" {
  source = "../../modules/ecr"

  project_name  = var.project_name
  environment   = var.environment
  service_names = ["incident-service", "timeline-service", "audit-worker"]
  force_delete  = true
}

# ECS Cluster
module "ecs_cluster" {
  source = "../../modules/ecs-cluster"

  project_name = var.project_name
  environment  = var.environment
}

# Application Load Balancer with target groups
module "alb" {
  source = "../../modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.networking.vpc_id
  subnet_ids        = module.networking.public_subnet_ids
  security_group_id = module.networking.alb_security_group_id

  enable_http2               = true
  enable_deletion_protection = false
  health_check_path          = "/health"
}

# ============================================================================
# PHASE 3: Data Layer - DynamoDB Tables
# ============================================================================

module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
}

# ============================================================================
# IAM Roles (Execution + Service-Specific Task Roles)
# ============================================================================

module "iam" {
  source = "../../modules/iam"

  project_name        = var.project_name
  environment         = var.environment
  ecr_repository_arns = module.ecr.repository_arns

  # DynamoDB tables (Phase 3)
  incidents_table_arn  = module.dynamodb.incidents_table_arn
  timeline_table_arn   = module.dynamodb.incident_timeline_table_arn
  audit_logs_table_arn = module.dynamodb.audit_logs_table_arn

  # EventBridge + SQS (placeholders for Phase 4)
  event_bus_arn   = ""
  audit_queue_arn = ""
}

# ============================================================================
# PHASE 2: HTTP Services (incident-service, timeline-service)
# Connected to ALB target groups
# ============================================================================

# incident-service
module "incident_service" {
  source = "../../modules/ecs-service"

  service_name    = "incident-service"
  cluster_name    = module.ecs_cluster.cluster_name
  container_image = "${module.ecr.repository_urls["incident-service"]}:dev"
  container_port  = var.container_port
  cpu             = var.service_cpu["incident-service"]
  memory          = var.service_memory["incident-service"]
  desired_count   = var.service_desired_count["incident-service"]

  environment_variables = {
    AWS_REGION           = var.aws_region
    INCIDENTS_TABLE_NAME = "cloud-incident-timeline-${var.environment}-incidents"
    EVENT_BUS_NAME       = "cloud-incident-timeline-${var.environment}-event-bus"
  }

  task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  task_role_arn           = module.iam.incident_service_task_role_arn

  log_group_name     = "/ecs/incident-service"
  log_retention_days = var.log_retention_days

  security_group_ids = [module.networking.ecs_security_group_id]
  subnet_ids         = module.networking.public_subnet_ids

  # Attach to ALB target group
  target_group_arn = module.alb.incident_target_group_arn
  assign_public_ip = true
  aws_region       = var.aws_region

  project_name = var.project_name
  environment  = var.environment
}

# timeline-service
module "timeline_service" {
  source = "../../modules/ecs-service"

  service_name    = "timeline-service"
  cluster_name    = module.ecs_cluster.cluster_name
  container_image = "${module.ecr.repository_urls["timeline-service"]}:dev"
  container_port  = var.container_port
  cpu             = var.service_cpu["timeline-service"]
  memory          = var.service_memory["timeline-service"]
  desired_count   = var.service_desired_count["timeline-service"]

  environment_variables = {
    AWS_REGION          = var.aws_region
    TIMELINE_TABLE_NAME = "cloud-incident-timeline-${var.environment}-incident_timeline"
  }

  task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  task_role_arn           = module.iam.timeline_service_task_role_arn

  log_group_name     = "/ecs/timeline-service"
  log_retention_days = var.log_retention_days

  security_group_ids = [module.networking.ecs_security_group_id]
  subnet_ids         = module.networking.public_subnet_ids

  # Attach to ALB target group
  target_group_arn = module.alb.timeline_target_group_arn
  assign_public_ip = true
  aws_region       = var.aws_region

  project_name = var.project_name
  environment  = var.environment
}

# ============================================================================
# PHASE 3: Data Layer
# DynamoDB tables, then update IAM
# ============================================================================

# Placeholder for Phase 3

# ============================================================================
# PHASE 4: Async Architecture
# EventBridge, SQS, audit-worker service
# ============================================================================

# Placeholder for Phase 4
