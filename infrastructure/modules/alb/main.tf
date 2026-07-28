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

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.security_group_id]
  subnets            = var.subnet_ids

  enable_deletion_protection = var.enable_deletion_protection
  enable_http2               = var.enable_http2

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-alb"
    }
  )
}

# HTTP Listener (port 80)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-http-listener"
    }
  )
}

# Target Group for incident-service
resource "aws_lb_target_group" "incident_service" {
  name        = "${local.name_prefix}-incident-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    path                = var.health_check_path
    matcher             = var.health_check_matcher
  }

  deregistration_delay = 30

  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-incident-tg"
      Service = "incident-service"
    }
  )
}

# Target Group for timeline-service
resource "aws_lb_target_group" "timeline_service" {
  name        = "${local.name_prefix}-timeline-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
    timeout             = var.health_check_timeout
    interval            = var.health_check_interval
    path                = var.health_check_path
    matcher             = var.health_check_matcher
  }

  deregistration_delay = 30

  tags = merge(
    local.common_tags,
    {
      Name    = "${local.name_prefix}-timeline-tg"
      Service = "timeline-service"
    }
  )
}

# Listener Rule 1: More specific path /incidents/*/timeline* → timeline-service
# Priority 100 (higher priority than the next rule)
resource "aws_lb_listener_rule" "timeline_service_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.timeline_service.arn
  }

  condition {
    path_pattern {
      values = ["/incidents/*/timeline*"]
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-timeline-rule"
    }
  )
}

# Listener Rule 2: General path /incidents* → incident-service
# Priority 200 (lower priority, matches general pattern)
resource "aws_lb_listener_rule" "incident_service_rule" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.incident_service.arn
  }

  condition {
    path_pattern {
      values = ["/incidents*"]
    }
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.name_prefix}-incident-rule"
    }
  )
}
