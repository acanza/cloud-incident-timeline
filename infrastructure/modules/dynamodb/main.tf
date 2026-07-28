# ============================================================================
# DynamoDB Module
# Three tables for Phase 3: incidents, incident_timeline, audit_logs
# ============================================================================

# ============================================================================
# Incidents Table
# Stores incident records created by incident-service
# ============================================================================

resource "aws_dynamodb_table" "incidents" {
  name         = "${var.project_name}-${var.environment}-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"

  attribute {
    name = "incident_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-incidents"
    Environment = var.environment
    Project     = var.project_name
    Module      = "dynamodb"
  }
}

# ============================================================================
# Incident Timeline Table
# Stores timeline events for each incident (accessed by timeline-service)
# PK: incident_id, SK: created_at (with event_id as regular attribute)
# ============================================================================

resource "aws_dynamodb_table" "incident_timeline" {
  name         = "${var.project_name}-${var.environment}-incident-timeline"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"
  range_key    = "created_at"

  attribute {
    name = "incident_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-incident-timeline"
    Environment = var.environment
    Project     = var.project_name
    Module      = "dynamodb"
  }
}

# ============================================================================
# Audit Logs Table
# Stores audit events processed by audit-worker from SQS
# PK: entity_id (what was audited), SK: created_at (with audit_id as regular attribute)
# ============================================================================

resource "aws_dynamodb_table" "audit_logs" {
  name         = "${var.project_name}-${var.environment}-audit-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "entity_id"
  range_key    = "created_at"

  attribute {
    name = "entity_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-audit-logs"
    Environment = var.environment
    Project     = var.project_name
    Module      = "dynamodb"
  }
}
