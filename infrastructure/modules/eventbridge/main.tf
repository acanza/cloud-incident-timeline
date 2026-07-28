# Custom EventBridge event bus
resource "aws_cloudwatch_event_bus" "main" {
  name = "${var.project_name}-${var.environment}-event-bus"
  tags = var.tags
}

# EventBridge rule to route incident events to SQS audit queue
resource "aws_cloudwatch_event_rule" "audit_events" {
  name           = "${var.project_name}-${var.environment}-audit-events-rule"
  description    = "Route incident events to audit queue"
  event_bus_name = aws_cloudwatch_event_bus.main.name

  event_pattern = jsonencode({
    source      = ["cloud-incident-timeline.incident-service"]
    detail-type = ["IncidentCreated", "IncidentStatusChanged"]
  })

  tags = var.tags
}

# SQS target for the EventBridge rule
resource "aws_cloudwatch_event_target" "audit_queue" {
  rule           = aws_cloudwatch_event_rule.audit_events.name
  event_bus_name = aws_cloudwatch_event_bus.main.name
  target_id      = "AuditQueue"
  arn            = var.audit_queue_arn

  # Allow EventBridge to send messages to the SQS queue
  role_arn = aws_iam_role.eventbridge_sqs_role.arn
}

# IAM role for EventBridge to put messages to SQS
resource "aws_iam_role" "eventbridge_sqs_role" {
  name               = "${var.project_name}-${var.environment}-eventbridge-sqs-role"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "eventbridge_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# IAM policy for EventBridge to send messages to SQS
resource "aws_iam_role_policy" "eventbridge_sqs_policy" {
  name   = "${var.project_name}-${var.environment}-eventbridge-sqs-policy"
  role   = aws_iam_role.eventbridge_sqs_role.id
  policy = data.aws_iam_policy_document.eventbridge_sqs_policy.json
}

data "aws_iam_policy_document" "eventbridge_sqs_policy" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:SendMessage"
    ]
    resources = [var.audit_queue_arn]
  }
}
