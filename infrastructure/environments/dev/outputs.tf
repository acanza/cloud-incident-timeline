# ============================================================================
# ALB Outputs
# ============================================================================

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.alb.alb_arn
}

# ============================================================================
# ECS Service Outputs
# ============================================================================

output "incident_service_arn" {
  description = "ARN of the incident-service ECS service"
  value       = module.incident_service.service_arn
}

output "timeline_service_arn" {
  description = "ARN of the timeline-service ECS service"
  value       = module.timeline_service.service_arn
}

output "incident_service_name" {
  description = "Name of the incident-service ECS service"
  value       = module.incident_service.service_name
}

output "timeline_service_name" {
  description = "Name of the timeline-service ECS service"
  value       = module.timeline_service.service_name
}

# ============================================================================
# Networking Outputs
# ============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.networking.public_subnet_ids
}

# ============================================================================
# ECR Outputs
# ============================================================================

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value       = module.ecr.repository_urls
}

# ============================================================================
# ECS Cluster Outputs
# ============================================================================

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs_cluster.cluster_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = module.ecs_cluster.cluster_arn
}

# ============================================================================
# Access Information
# ============================================================================

output "access_info" {
  description = "How to access the services"
  value = {
    alb_dns               = module.alb.alb_dns_name
    incident_service_url  = "http://${module.alb.alb_dns_name}/incidents"
    timeline_service_url  = "http://${module.alb.alb_dns_name}/incidents/{incidentId}/timeline"
    incident_health_check = "http://${module.alb.alb_dns_name}/health"
  }
}

# ============================================================================
# Phase 3: DynamoDB Tables Outputs
# ============================================================================

output "dynamodb_table_names" {
  description = "DynamoDB table names by service"
  value       = module.dynamodb.table_names
}

output "dynamodb_table_arns" {
  description = "DynamoDB table ARNs by service"
  value       = module.dynamodb.table_arns
}

output "incidents_table_name" {
  description = "Name of the incidents table"
  value       = module.dynamodb.incidents_table_name
}

output "incident_timeline_table_name" {
  description = "Name of the incident_timeline table"
  value       = module.dynamodb.incident_timeline_table_name
}

output "audit_logs_table_name" {
  description = "Name of the audit_logs table"
  value       = module.dynamodb.audit_logs_table_name
}

# ============================================================================
# Phase 4: Async Architecture Outputs
# ============================================================================

output "audit_worker_service_arn" {
  description = "ARN of the audit-worker ECS service"
  value       = module.audit_worker.service_arn
}

output "audit_worker_service_name" {
  description = "Name of the audit-worker ECS service"
  value       = module.audit_worker.service_name
}

output "eventbridge_event_bus_name" {
  description = "Name of the custom EventBridge event bus"
  value       = module.eventbridge.event_bus_name
}

output "eventbridge_event_bus_arn" {
  description = "ARN of the custom EventBridge event bus"
  value       = module.eventbridge.event_bus_arn
}

output "eventbridge_audit_rule_name" {
  description = "Name of the EventBridge rule for audit events"
  value       = module.eventbridge.audit_rule_name
}

output "audit_queue_url" {
  description = "URL of the audit SQS queue"
  value       = module.sqs.audit_queue_url
}

output "audit_queue_arn" {
  description = "ARN of the audit SQS queue"
  value       = module.sqs.audit_queue_arn
}

output "audit_dlq_url" {
  description = "URL of the audit dead-letter queue"
  value       = module.sqs.audit_dlq_url
}

output "audit_dlq_arn" {
  description = "ARN of the audit dead-letter queue"
  value       = module.sqs.audit_dlq_arn
}
