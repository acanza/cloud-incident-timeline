variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cloud-incident-timeline"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "service_cpu" {
  description = "CPU units per service"
  type        = map(number)
  default = {
    incident-service = 256
    timeline-service = 256
    audit-worker     = 256
  }
}

variable "service_memory" {
  description = "Memory MB per service"
  type        = map(number)
  default = {
    incident-service = 512
    timeline-service = 512
    audit-worker     = 512
  }
}

variable "service_desired_count" {
  description = "Desired count per service"
  type        = map(number)
  default = {
    incident-service = 1
    timeline-service = 1
    audit-worker     = 1
  }
}

variable "container_port" {
  description = "Container port for HTTP services"
  type        = number
  default     = 3000
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period"
  type        = number
  default     = 3
}
