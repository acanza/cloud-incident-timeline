locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      Terraform   = "true"
      Service     = var.service_name
    }
  )
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "service" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days

  tags = merge(
    local.common_tags,
    {
      Name = var.log_group_name
    }
  )
}

# ECS Task Definition
resource "aws_ecs_task_definition" "service" {
  family                   = "${local.name_prefix}-${var.service_name}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = var.container_image
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        for key, value in var.environment_variables :
        {
          name  = key
          value = value
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.service.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      # Health check for the container (optional, can be used by services)
      # This is in addition to ALB health checks for HTTP services
      healthCheck = {
        command     = ["CMD-SHELL", "test -f /tmp/healthy || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 0
      }
    }
  ])

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-${var.service_name}-task"
    }
  )
}

# ECS Service
resource "aws_ecs_service" "service" {
  name            = "${local.name_prefix}-${var.service_name}"
  cluster         = var.cluster_name
  task_definition = aws_ecs_task_definition.service.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = var.assign_public_ip
  }

  # Conditionally attach to target group if provided (for HTTP services)
  dynamic "load_balancer" {
    for_each = var.target_group_arn != null ? [1] : []

    content {
      target_group_arn = var.target_group_arn
      container_name   = var.service_name
      container_port   = var.container_port
    }
  }

  # Rolling deployment strategy settings
  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100

  depends_on = [aws_cloudwatch_log_group.service]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-${var.service_name}"
    }
  )

  lifecycle {
    ignore_changes = [desired_count] # Allow external autoscaling to modify this
  }
}

# Data source for current AWS account and region
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}
