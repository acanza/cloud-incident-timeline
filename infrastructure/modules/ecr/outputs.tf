output "repository_urls" {
  description = "Map of service names to ECR repository URLs (without tag)"
  value = {
    for service, repo in aws_ecr_repository.service :
    service => repo.repository_url
  }
}

output "repository_arns" {
  description = "Map of service names to ECR repository ARNs"
  value = {
    for service, repo in aws_ecr_repository.service :
    service => repo.arn
  }
}

output "repositories" {
  description = "Map of all ECR repositories with full details"
  value = {
    for service, repo in aws_ecr_repository.service :
    service => {
      name           = repo.name
      url            = repo.repository_url
      arn            = repo.arn
      registry_id    = repo.registry_id
      repository_uri = repo.repository_url
    }
  }
}
