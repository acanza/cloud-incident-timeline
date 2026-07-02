# Cost Control Specification

## Goal

The infrastructure must be suitable for temporary deployments.

The expected workflow is:

```bash
terraform apply
# run tests
terraform destroy
```

## Cost-control decisions

For v0.1:

- Do not create NAT Gateway.
- Do not create Route 53 records.
- Do not create ACM certificates.
- Do not enable HTTPS.
- Do not create private subnets.
- Do not enable ECS autoscaling.
- Do not use high CPU or memory values.
- Do not set desired count above 1.
- Use DynamoDB pay-per-request.
- Use short CloudWatch log retention.
- Use ECR force delete.
- Avoid unnecessary VPC endpoints.

## ECS defaults

Use:
```hcl
cpu           = 256
memory        = 512
desired_count = 1
```

## Log retention

Use short retention for CloudWatch Logs.

Recommended:

```hcl
retention_in_days = 3
```

## Destroy requirements

The following resources should not block terraform destroy:

- ECR repositories.
- CloudWatch Log Groups.
- ALB.
- ECS services.
- DynamoDB tables.
- SQS queues.