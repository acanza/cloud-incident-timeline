variable "service_name" {
  description = "Name of the ECS service"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.service_name))
    error_message = "Service name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "container_image" {
  description = "Docker image URI for the container (e.g., <account_id>.dkr.ecr.<region>.amazonaws.com/<repo>:tag)"
  type        = string
  validation {
    condition     = can(regex(".*:.*", var.container_image))
    error_message = "Container image must include a tag (e.g., image:dev)."
  }
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  validation {
    condition     = var.container_port > 0 && var.container_port <= 65535
    error_message = "Container port must be between 1 and 65535."
  }
}

variable "cpu" {
  description = "Task CPU units (256, 512, 1024, etc.)"
  type        = number
  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU must be 256, 512, 1024, 2048, or 4096."
  }
}

variable "memory" {
  description = "Task memory in MB (512, 1024, 2048, etc.)"
  type        = number
  validation {
    condition     = var.memory >= 512 && var.memory <= 30720
    error_message = "Memory must be between 512 and 30720 MB."
  }
}

variable "desired_count" {
  description = "Number of desired task instances"
  type        = number
  default     = 1
  validation {
    condition     = var.desired_count > 0
    error_message = "Desired count must be at least 1."
  }
}

variable "environment_variables" {
  description = "Map of environment variables for the container"
  type        = map(string)
  default     = {}
}

variable "task_execution_role_arn" {
  description = "ARN of the IAM role for task execution (ECR pull, CloudWatch Logs)"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the IAM role for task permissions (DynamoDB, SQS, EventBridge, etc.)"
  type        = string
}

variable "log_group_name" {
  description = "CloudWatch Log Group name"
  type        = string
  validation {
    condition     = can(regex("^/[a-zA-Z0-9/_.-]+$", var.log_group_name))
    error_message = "Log group name must start with / and contain only alphanumeric characters, slashes, underscores, dots, and hyphens."
  }
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 3
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be one of AWS's supported values."
  }
}

variable "security_group_ids" {
  description = "List of security group IDs for the service"
  type        = list(string)
  validation {
    condition     = length(var.security_group_ids) > 0
    error_message = "Must provide at least one security group ID."
  }
}

variable "subnet_ids" {
  description = "List of subnet IDs for task placement"
  type        = list(string)
  validation {
    condition     = length(var.subnet_ids) > 0
    error_message = "Must provide at least one subnet ID."
  }
}

variable "target_group_arn" {
  description = "Target group ARN for ALB integration (optional, for HTTP services)"
  type        = string
  default     = null
}

variable "assign_public_ip" {
  description = "Assign public IP to tasks (true for public subnets, false for private)"
  type        = bool
  default     = true
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
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

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
