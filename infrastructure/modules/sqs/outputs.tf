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
