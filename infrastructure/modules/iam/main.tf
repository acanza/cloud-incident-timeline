locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      Terraform   = "true"
    }
  )
}

# Trust policy for ECS tasks
data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# ============================================================================
# Shared ECS Task Execution Role (for all services)
# Allows: ECR image pull, CloudWatch Logs write
# ============================================================================

resource "aws_iam_role" "ecs_task_execution_role" {
  name_prefix           = "${local.name_prefix}-ecs-task-exec-"
  assume_role_policy    = data.aws_iam_policy_document.ecs_task_assume.json
  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-ecs-task-execution-role"
    }
  )
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ============================================================================
# incident-service Task Role
# Permissions: incidents table (read/write), EventBridge (PutEvents)
# ============================================================================

resource "aws_iam_role" "incident_service_task_role" {
  name_prefix        = "${local.name_prefix}-incident-service-task-"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-incident-service-task-role"
      Service = "incident-service"
    }
  )
}

data "aws_iam_policy_document" "incident_service_task_policy" {
  statement {
    sid       = "DynamoDBIncidentsAccess"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:Scan"]
    resources = [var.incidents_table_arn]
  }

  statement {
    sid       = "EventBridgePutEvents"
    actions   = ["events:PutEvents"]
    resources = [var.event_bus_arn != "" ? var.event_bus_arn : "arn:aws:events:*:*:event-bus/${local.name_prefix}-event-bus"]
  }
}

resource "aws_iam_role_policy" "incident_service_task_policy" {
  name_prefix = "${local.name_prefix}-incident-service-"
  role        = aws_iam_role.incident_service_task_role.id
  policy      = data.aws_iam_policy_document.incident_service_task_policy.json
}

# ============================================================================
# timeline-service Task Role
# Permissions: incident_timeline table (read/write)
# ============================================================================

resource "aws_iam_role" "timeline_service_task_role" {
  name_prefix        = "${local.name_prefix}-timeline-service-task-"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-timeline-service-task-role"
      Service = "timeline-service"
    }
  )
}

data "aws_iam_policy_document" "timeline_service_task_policy" {
  statement {
    sid       = "DynamoDBTimelineAccess"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:Scan"]
    resources = [var.timeline_table_arn]
  }
}

resource "aws_iam_role_policy" "timeline_service_task_policy" {
  name_prefix = "${local.name_prefix}-timeline-service-"
  role        = aws_iam_role.timeline_service_task_role.id
  policy      = data.aws_iam_policy_document.timeline_service_task_policy.json
}

# ============================================================================
# audit-worker Task Role
# Permissions: audit SQS queue (receive/delete), audit_logs table (write)
# ============================================================================

resource "aws_iam_role" "audit_worker_task_role" {
  name_prefix        = "${local.name_prefix}-audit-worker-task-"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json

  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-audit-worker-task-role"
      Service = "audit-worker"
    }
  )
}

data "aws_iam_policy_document" "audit_worker_task_policy" {
  statement {
    sid     = "SQSAuditQueueAccess"
    actions = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [
      var.audit_queue_arn != "" ? var.audit_queue_arn : "arn:aws:sqs:*:*:${local.name_prefix}-audit-queue"
    ]
  }

  statement {
    sid       = "DynamoDAuditLogsAccess"
    actions   = ["dynamodb:PutItem"]
    resources = [var.audit_logs_table_arn]
  }
}

resource "aws_iam_role_policy" "audit_worker_task_policy" {
  name_prefix = "${local.name_prefix}-audit-worker-"
  role        = aws_iam_role.audit_worker_task_role.id
  policy      = data.aws_iam_policy_document.audit_worker_task_policy.json
}
