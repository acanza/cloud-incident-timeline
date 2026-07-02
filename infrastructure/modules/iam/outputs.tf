output "ecs_task_execution_role_arn" {
  description = "ARN of the shared ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "incident_service_task_role_arn" {
  description = "ARN of the incident-service task role"
  value       = aws_iam_role.incident_service_task_role.arn
}

output "timeline_service_task_role_arn" {
  description = "ARN of the timeline-service task role"
  value       = aws_iam_role.timeline_service_task_role.arn
}

output "audit_worker_task_role_arn" {
  description = "ARN of the audit-worker task role"
  value       = aws_iam_role.audit_worker_task_role.arn
}
