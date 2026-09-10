# Deployment Guide

## Prerequisites

- **AWS Account** with credentials configured locally (`~/.aws/credentials`)
- **Terraform** >= 1.0
- **Docker** (for building service images)
- **AWS CLI** v2

Verify:
```bash
aws sts get-caller-identity  # Confirm AWS access
terraform version             # Verify Terraform
```

## Environment Setup

### 1. Configure AWS Credentials

```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (eu-west-3), Output format (json)
```

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="eu-west-3"
```

### 2. Review Variables (Optional)

Default dev configuration is in:
```
infrastructure/environments/dev/terraform.tfvars
```

To override, edit values or use `-var` flags in `terraform apply`.

## Deployment Workflow

### Step 1: Initialize Terraform

```bash
cd infrastructure/environments/dev
terraform init
```

This downloads provider plugins and prepares the backend.

### Step 2: Format & Validate

```bash
make fmt validate
```

Ensures code quality and catches syntax errors.

### Step 3: Review Plan

```bash
make plan
```

Shows all resources that will be created. **Review carefully** for:
- Correct region (eu-west-3)
- Correct VPC CIDR (10.20.0.0/16)
- 3 ECS services (incident-service, timeline-service, audit-worker)
- 1 DynamoDB table per service
- EventBridge custom bus + SQS queue

### Step 4: Apply Changes

```bash
make apply
```

**Requires confirmation:** Type `yes` when prompted.

Deployment typically takes **3-5 minutes**. Monitor output for:
- ALB DNS name
- ECS service endpoints
- DynamoDB table names

## Post-Deployment Validation

### Check Infrastructure Status

```bash
# List all resources
make state-list

# Show outputs (ALB DNS, etc.)
make output
```

### Verify Services are Running

```bash
# Get ALB DNS name from outputs
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test health endpoints
curl http://$ALB_DNS/health

# Test incident service
curl http://$ALB_DNS/incidents

# Test timeline service
curl http://$ALB_DNS/incidents/test-id/timeline
```

Expected responses: 200 OK with JSON.

### Check CloudWatch Logs

```bash
aws logs tail /cloud-incident-timeline-dev/incident-service --follow
aws logs tail /cloud-incident-timeline-dev/timeline-service --follow
aws logs tail /cloud-incident-timeline-dev/audit-worker --follow
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Terraform init fails** | Check AWS credentials: `aws sts get-caller-identity` |
| **Plan shows unsupported region** | Verify `aws_region` in variables.tf matches your account's availability |
| **Services show "unhealthy"** | Wait 2-3 minutes for ECS deployment. Check CloudWatch logs for errors. |
| **ALB not responding** | Confirm ALB security group allows inbound on port 80 from 0.0.0.0/0 |
| **DynamoDB access denied** | Verify task IAM role has DynamoDB permissions (check in apply output) |

## Cleanup

See [DESTROY.md](./DESTROY.md) for safe removal of all resources.
