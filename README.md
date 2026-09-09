# Cloud Incident Timeline

**Learning Project** — Microservices + Event-Driven Architecture on AWS

## About

A hands-on project to learn:
- **Microservices architecture** — Multiple independent services communicating via APIs
- **Event-driven patterns** — Async communication using EventBridge and SQS
- **Infrastructure as Code** — Terraform on AWS (ECS, DynamoDB, ALB)

## Tech Stack

- **Services**: Python 3.11, FastAPI
- **Container Runtime**: ECS Fargate
- **Data**: DynamoDB (NoSQL)
- **Messaging**: EventBridge, SQS
- **API Gateway**: Application Load Balancer (ALB)
- **Infrastructure**: Terraform

## Project Structure

```
.
├── infrastructure/          # Terraform modules & environments
│   ├── modules/            # Reusable AWS components
│   └── environments/dev/    # Dev environment configuration
├── services/               # Microservices
│   ├── incident-service/   # HTTP API for incident management
│   ├── timeline-service/   # HTTP API for incident timeline
│   └── audit-worker/       # Async worker for audit logs
└── .github/specs/          # Architecture & implementation specs
```

## Quick Start

```bash
# 1. Set up infrastructure
cd infrastructure/environments/dev
terraform init
terraform plan
terraform apply

# 2. Deploy services (see deployment guide)
# 3. Test endpoints (see service README files)
```

## Documentation

- [**Deployment Guide**](./docs/DEPLOYMENT.md) — Step-by-step deployment
- [**Destroy Guide**](./docs/DESTROY.md) — Cleanup procedures
- [**Architecture**](./docs/ARCHITECTURE.md) — System design & flows
- [Service READMEs](./services/) — API contracts & testing
