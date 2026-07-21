# ============================================================================
# Outputs: Table names and ARNs for use by ECS services and IAM policies
# ============================================================================

output "incidents_table_name" {
  description = "Name of the incidents table"
  value       = aws_dynamodb_table.incidents.name
}

output "incidents_table_arn" {
  description = "ARN of the incidents table"
  value       = aws_dynamodb_table.incidents.arn
}

output "incident_timeline_table_name" {
  description = "Name of the incident timeline table"
  value       = aws_dynamodb_table.incident_timeline.name
}

output "incident_timeline_table_arn" {
  description = "ARN of the incident timeline table"
  value       = aws_dynamodb_table.incident_timeline.arn
}

output "audit_logs_table_name" {
  description = "Name of the audit logs table"
  value       = aws_dynamodb_table.audit_logs.name
}

output "audit_logs_table_arn" {
  description = "ARN of the audit logs table"
  value       = aws_dynamodb_table.audit_logs.arn
}

# Convenience mapping: table names and ARNs
output "table_names" {
  description = "Map of all table names by service"
  value = {
    incidents         = aws_dynamodb_table.incidents.name
    incident_timeline = aws_dynamodb_table.incident_timeline.name
    audit_logs        = aws_dynamodb_table.audit_logs.name
  }
}

output "table_arns" {
  description = "Map of all table ARNs by service"
  value = {
    incidents         = aws_dynamodb_table.incidents.arn
    incident_timeline = aws_dynamodb_table.incident_timeline.arn
    audit_logs        = aws_dynamodb_table.audit_logs.arn
  }
}
