variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, stage, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "Environment must be dev, stage, or prod."
  }
}

variable "ecr_repository_arns" {
  description = "Map of service names to ECR repository ARNs"
  type        = map(string)
}

variable "incidents_table_arn" {
  description = "ARN of the incidents DynamoDB table"
  type        = string
  default     = ""
}

variable "timeline_table_arn" {
  description = "ARN of the incident_timeline DynamoDB table"
  type        = string
  default     = ""
}

variable "audit_logs_table_arn" {
  description = "ARN of the audit_logs DynamoDB table"
  type        = string
  default     = ""
}

variable "event_bus_arn" {
  description = "ARN of the EventBridge event bus"
  type        = string
  default     = ""
}

variable "audit_queue_arn" {
  description = "ARN of the audit SQS queue"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
