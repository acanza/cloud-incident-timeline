# Destroy Guide

## Cost-Control Principle

This project is designed for **temporary deployments**. After testing/learning:

```bash
terraform apply   # Deploy
# run tests
terraform destroy # Clean up
```

Expected cost: **~$2-5 USD** per day on AWS free tier.

## Before You Destroy

### ⚠️ Data Loss Warning

Destroying infrastructure will **permanently delete**:
- DynamoDB tables (incidents, timeline, audit_logs)
- SQS messages (any queued events)
- CloudWatch Logs (all service logs)
- ALB and target groups

**Data cannot be recovered** unless you create backups first.

### Backup Strategy (Optional)

If you need to preserve data:

```bash
# Export DynamoDB tables to JSON
aws dynamodb scan --table-name cloud-incident-timeline-dev-incidents \
  --output json > incidents-backup.json

aws dynamodb scan --table-name cloud-incident-timeline-dev-incident-timeline \
  --output json > timeline-backup.json

aws dynamodb scan --table-name cloud-incident-timeline-dev-audit-logs \
  --output json > audit-backup.json
```

## Destroy Workflow

### Step 1: Verify Deployment Status

```bash
make state-list
make output
```

Confirms you're destroying the correct environment.

### Step 2: Run Destroy

```bash
make destroy
```

**Requires explicit confirmation:**
```
Type 'destroy-dev' to confirm:
```

Type exactly: `destroy-dev` (prevents accidental deletion)

Destruction typically takes **2-3 minutes**.

### Step 3: Verify Cleanup

```bash
# Confirm all resources removed
aws ec2 describe-vpcs --filters "Name=cidr,Values=10.20.0.0/16"
# Should return: VpcsNotFound

# Confirm DynamoDB tables gone
aws dynamodb list-tables
# Should NOT show cloud-incident-timeline-* tables
```

## Cleanup Residual Resources

Terraform should remove all resources. If any remain (due to manual changes):

### CloudWatch Logs

```bash
aws logs delete-log-group --log-group-name /cloud-incident-timeline-dev/incident-service
aws logs delete-log-group --log-group-name /cloud-incident-timeline-dev/timeline-service
aws logs delete-log-group --log-group-name /cloud-incident-timeline-dev/audit-worker
```

### ECR Repositories

```bash
aws ecr delete-repository --repository-name cloud-incident-timeline-dev-incident-service --force
aws ecr delete-repository --repository-name cloud-incident-timeline-dev-timeline-service --force
aws ecr delete-repository --repository-name cloud-incident-timeline-dev-audit-worker --force
```

### Local Cleanup

```bash
# Remove Terraform state and cache
make clean

# Remove local build artifacts
cd infrastructure/environments/dev && rm -f tfplan terraform.tfstate*
```

## Cost Control Summary

### Decisions Made for Minimal Cost

| Decision | Cost Impact |
|----------|-------------|
| **No NAT Gateway** | Saves $32/month (NAT charges) |
| **Public subnets only** | Minimal data transfer costs |
| **ECS Fargate CPU 256** | $0.015/hour per task |
| **DynamoDB on-demand** | ~$1.25 per GB written |
| **CloudWatch 3-day retention** | Minimal log storage |
| **No autoscaling** | 1 task per service = predictable cost |
| **No Route 53** | Saves $0.50/hosted zone |
| **No ACM/HTTPS** | Reduces complexity, cost |

### Estimated Daily Cost (Dev)

With default settings and light testing:
- **ECS Fargate**: ~$1-2/day (3 tasks × $0.015/hour)
- **DynamoDB**: ~$0-1/day (on-demand, minimal writes)
- **ALB**: ~$0.50/day (fixed hourly charge)
- **CloudWatch**: ~$0.10/day (minimal logs, short retention)
- **Data Transfer**: ~$0/day (internal AWS)

**Total: ~$2-5/day** on AWS free tier

To minimize costs further:
- Destroy after each testing session
- Test during free tier hours
- Monitor CloudWatch billing alerts

## Re-deployment

To deploy again after destruction:

```bash
cd infrastructure/environments/dev
terraform init    # Re-initialize (cached files cleared)
terraform plan    # Review
make apply        # Deploy
```

All resources will be recreated with fresh state.
