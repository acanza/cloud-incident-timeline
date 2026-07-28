# Dead-letter queue for failed audit messages
resource "aws_sqs_queue" "audit_dlq" {
  name                      = "${var.project_name}-${var.environment}-audit-dlq"
  message_retention_seconds = 1209600  # 14 days
  tags                      = var.tags
}

# Main audit queue with redrive policy pointing to DLQ
resource "aws_sqs_queue" "audit_queue" {
  name                       = "${var.project_name}-${var.environment}-audit-queue"
  visibility_timeout_seconds = 300  # 5 minutes
  message_retention_seconds  = 86400  # 1 day
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.audit_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })
  
  tags = var.tags
}
