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

### Getting Started
- [**Architecture**](./docs/ARCHITECTURE.md) — Complete system design with diagrams
- [**Deployment Guide**](./docs/DEPLOYMENT.md) — Prerequisites, setup, validation
- [**Destroy Guide**](./docs/DESTROY.md) — Safe cleanup, backup strategy

### Service Documentation
- [incident-service](./services/incident-service/README.md) — REST API for incident CRUD
- [timeline-service](./services/timeline-service/README.md) — Timeline queries & comments
- [audit-worker](./services/audit-worker/README.md) — Event processing & audit logs

### Comprehensive Checklist
- [**Phase 5: Documentation Completion**](./docs/PHASE_5_COMPLETION.md) — All documentation verified & complete

### Specifications (Deep Dive)
- [Project Context](./github/specs/00-project-context.md)
- [Architecture Spec](./github/specs/01-architecture.md)
- [Data & Events](./github/specs/06-data-and-events.md)
- [Cost Control](./github/specs/07-cost-control.md)
