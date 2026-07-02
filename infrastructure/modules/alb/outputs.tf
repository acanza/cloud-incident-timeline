output "alb_id" {
  description = "ALB ID"
  value       = aws_lb.main.id
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the ALB"
  value       = aws_lb.main.zone_id
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}

output "incident_target_group_arn" {
  description = "ARN of the incident-service target group"
  value       = aws_lb_target_group.incident_service.arn
}

output "incident_target_group_name" {
  description = "Name of the incident-service target group"
  value       = aws_lb_target_group.incident_service.name
}

output "timeline_target_group_arn" {
  description = "ARN of the timeline-service target group"
  value       = aws_lb_target_group.timeline_service.arn
}

output "timeline_target_group_name" {
  description = "Name of the timeline-service target group"
  value       = aws_lb_target_group.timeline_service.name
}

output "target_groups" {
  description = "Map of all target groups with their details"
  value = {
    incident_service = {
      arn  = aws_lb_target_group.incident_service.arn
      name = aws_lb_target_group.incident_service.name
    }
    timeline_service = {
      arn  = aws_lb_target_group.timeline_service.arn
      name = aws_lb_target_group.timeline_service.name
    }
  }
}
