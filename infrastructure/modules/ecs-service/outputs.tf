output "service_id" {
  description = "ECS Service ID"
  value       = aws_ecs_service.service.id
}

output "service_name" {
  description = "ECS Service name"
  value       = aws_ecs_service.service.name
}

output "service_arn" {
  description = "ECS Service ARN"
  value       = "arn:aws:ecs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:service/${var.cluster_name}/${aws_ecs_service.service.name}"
}

output "task_definition_arn" {
  description = "ECS Task Definition ARN"
  value       = aws_ecs_task_definition.service.arn
}

output "task_definition_family" {
  description = "ECS Task Definition family name"
  value       = aws_ecs_task_definition.service.family
}

output "log_group_name" {
  description = "CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.service.name
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN"
  value       = aws_cloudwatch_log_group.service.arn
}
