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
    alb_dns                 = module.alb.alb_dns_name
    incident_service_url    = "http://${module.alb.alb_dns_name}/incidents"
    timeline_service_url    = "http://${module.alb.alb_dns_name}/incidents/{incidentId}/timeline"
    incident_health_check   = "http://${module.alb.alb_dns_name}/health"
  }
}
