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

# ECR repositories for each service
resource "aws_ecr_repository" "service" {
  for_each = toset(var.service_names)

  repository_name = "${local.name_prefix}-${each.value}"
  force_delete    = var.force_delete

  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-${each.value}"
      Service = each.value
    }
  )
}
