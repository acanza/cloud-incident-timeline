# Custom EventBridge event bus
resource "aws_cloudwatch_event_bus" "main" {
  name = "${var.project_name}-${var.environment}-event-bus"
  tags = var.tags
}

# ============================================================================
# Timeline Queue Routing
# ============================================================================

# EventBridge rule to route incident events to SQS timeline queue
resource "aws_cloudwatch_event_rule" "timeline_events" {
  name           = "${var.project_name}-${var.environment}-timeline-events-rule"
  description    = "Route incident events to timeline queue"
  event_bus_name = aws_cloudwatch_event_bus.main.name

  event_pattern = jsonencode({
    source = ["cloud-incident-timeline.incident-service"]
    detail-type = [
      "IncidentCreated",
      "IncidentStatusChanged",
      "IncidentSeverityChanged",
      "IncidentResolved"
    ]
  })

  tags = var.tags
}

# SQS target for the timeline EventBridge rule
resource "aws_cloudwatch_event_target" "timeline_queue" {
  rule           = aws_cloudwatch_event_rule.timeline_events.name
  event_bus_name = aws_cloudwatch_event_bus.main.name
  target_id      = "TimelineQueue"
  arn            = var.timeline_queue_arn

  # Allow EventBridge to send messages to the SQS queue
  role_arn = aws_iam_role.eventbridge_sqs_role.arn
}

# ============================================================================
# Audit Queue Routing
# ============================================================================

# EventBridge rule to route incident events to SQS audit queue
resource "aws_cloudwatch_event_rule" "audit_events" {
  name           = "${var.project_name}-${var.environment}-audit-events-rule"
  description    = "Route incident events to audit queue"
  event_bus_name = aws_cloudwatch_event_bus.main.name

  event_pattern = jsonencode({
    source = [
      "cloud-incident-timeline.incident-service",
      "cloud-incident-timeline.timeline-service"
    ]
    detail-type = [
      "IncidentCreated",
      "IncidentStatusChanged",
      "IncidentSeverityChanged",
      "IncidentResolved",
      "TimelineCommentAdded"
    ]
  })

  tags = var.tags
}

# SQS target for the audit EventBridge rule
resource "aws_cloudwatch_event_target" "audit_queue" {
  rule           = aws_cloudwatch_event_rule.audit_events.name
  event_bus_name = aws_cloudwatch_event_bus.main.name
  target_id      = "AuditQueue"
  arn            = var.audit_queue_arn

  # Allow EventBridge to send messages to the SQS queue
  role_arn = aws_iam_role.eventbridge_sqs_role.arn
}

# ============================================================================
# Shared IAM Role for EventBridge to SQS
# ============================================================================

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

# IAM policy for EventBridge to send messages to both SQS queues
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
    resources = [
      var.timeline_queue_arn,
      var.audit_queue_arn
    ]
  }
}
