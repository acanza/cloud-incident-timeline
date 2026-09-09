output "timeline_queue_url" {
  description = "URL of the timeline queue"
  value       = aws_sqs_queue.timeline_queue.url
}

output "timeline_queue_arn" {
  description = "ARN of the timeline queue"
  value       = aws_sqs_queue.timeline_queue.arn
}

output "timeline_dlq_url" {
  description = "URL of the timeline dead-letter queue"
  value       = aws_sqs_queue.timeline_dlq.url
}

output "timeline_dlq_arn" {
  description = "ARN of the timeline dead-letter queue"
  value       = aws_sqs_queue.timeline_dlq.arn
}

output "audit_queue_url" {
  description = "URL of the audit queue"
  value       = aws_sqs_queue.audit_queue.url
}

output "audit_queue_arn" {
  description = "ARN of the audit queue"
  value       = aws_sqs_queue.audit_queue.arn
}

output "audit_dlq_url" {
  description = "URL of the audit dead-letter queue"
  value       = aws_sqs_queue.audit_dlq.url
}

output "audit_dlq_arn" {
  description = "ARN of the audit dead-letter queue"
  value       = aws_sqs_queue.audit_dlq.arn
}
