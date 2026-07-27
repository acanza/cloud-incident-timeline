# ============================================================================
# DynamoDB Module
# Three tables for Phase 3: incidents, incident_timeline, audit_logs
# ============================================================================

# ============================================================================
# Incidents Table
# Stores incident records created by incident-service
# ============================================================================

resource "aws_dynamodb_table" "incidents" {
  name           = "${var.project_name}-${var.environment}-incidents"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "incident_id"
  
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
# ============================================================================

resource "aws_dynamodb_table" "incident_timeline" {
  name           = "${var.project_name}-${var.environment}-incident-timeline"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "incident_id"
  range_key      = "timestamp"
  
  attribute {
    name = "incident_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
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
# ============================================================================

resource "aws_dynamodb_table" "audit_logs" {
  name           = "${var.project_name}-${var.environment}-audit-logs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "audit_id"
  
  attribute {
    name = "audit_id"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-audit-logs"
    Environment = var.environment
    Project     = var.project_name
    Module      = "dynamodb"
  }
}
