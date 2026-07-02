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

variable "service_names" {
  description = "List of service names for which to create ECR repositories"
  type        = list(string)
  validation {
    condition     = length(var.service_names) > 0
    error_message = "Must provide at least one service name."
  }
}

variable "force_delete" {
  description = "Allow deletion of non-empty ECR repositories (for dev/test environments)"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
