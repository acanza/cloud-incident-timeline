variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "timeline_queue_arn" {
  description = "ARN of the timeline SQS queue"
  type        = string
}

variable "audit_queue_arn" {
  description = "ARN of the audit SQS queue"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
