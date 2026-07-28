output "event_bus_name" {
  description = "Name of the custom EventBridge event bus"
  value       = aws_cloudwatch_event_bus.main.name
}

output "event_bus_arn" {
  description = "ARN of the custom EventBridge event bus"
  value       = aws_cloudwatch_event_bus.main.arn
}

output "audit_rule_name" {
  description = "Name of the audit events EventBridge rule"
  value       = aws_cloudwatch_event_rule.audit_events.name
}

output "audit_rule_arn" {
  description = "ARN of the audit events EventBridge rule"
  value       = aws_cloudwatch_event_rule.audit_events.arn
}
