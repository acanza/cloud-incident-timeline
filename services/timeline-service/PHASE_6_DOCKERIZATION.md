# Timeline Service - Phase 6: Dockerization & Multi-Process Orchestration

## Overview

Fase 6 empaqueta el timeline-service (FastAPI HTTP API + SQS Consumer) en una imagen Docker optimizada para ECS/Fargate.

## Architecture

```
Docker Image (timeline-service:dev)
├─ Python 3.11 Runtime
├─ Dependencies (FastAPI, Boto3, etc.)
├─ Application Code
└─ Orchestration Layer
   ├─ Entrypoint Script
   ├─ FastAPI HTTP Server (Port 8080)
   └─ SQS Consumer (Background Process)
```

## Why Multi-Process Orchestration?

El timeline-service necesita ejecutar **dos procesos concurrentemente**:

1. **FastAPI HTTP Server** - Expone endpoints REST al ALB
   - Maneja: GET /health, GET /incidents/{id}/timeline, POST comments
   - ALB espera /health en puerto 8080

2. **SQS Consumer** - Procesa eventos en background
   - Polea la queue de SQS
   - Escribe timeline entries en DynamoDB
   - Graceful shutdown on SIGTERM

**Nota:** No pueden ser servicios ECS separados porque:
- SQS Consumer requiere acceso a la misma DynamoDB table
- Ambos necesitan la misma configuración (credenciales, variables de entorno)
- La arquitectura del proyecto los está diseñados para coexistir

## Image Design

### Multi-Stage Build

```dockerfile
Stage 1: Builder
  ├─ Python 3.11
  ├─ Build tools
  └─ Install dependencies

Stage 2: Runtime
  ├─ Python 3.11 (slim)
  ├─ Copy dependencies from builder
  ├─ Copy application code
  └─ ~200MB final image size
```

**Beneficios:**
- Imagen final más pequeña (~200MB vs 500MB)
- Reduce tiempo de pull en ECS
- Reduce costo de almacenamiento en ECR
- Mantiene capacidad de ejecución completa

### Entrypoint Orchestration

`entrypoint.sh` orquesta los procesos:

```bash
1. Validate configuration
2. Start FastAPI server → background
3. Wait 2s for FastAPI startup
4. Start SQS Consumer → background
5. Register signal handlers (SIGTERM, SIGINT)
6. Wait para ambos procesos

Signal Handler:
  SIGTERM/SIGINT → 
    Kill FastAPI (TERM signal)
    Kill Consumer (TERM signal)
    Wait for both
    Exit cleanly
```

**Graceful Shutdown:**
- ECS sends SIGTERM to container
- Entrypoint catches signal
- FastAPI completes current request then stops
- SQS Consumer completes current message then stops
- Container exits with code 0 (success)

### Health Check

Dockerfile incluye HEALTHCHECK:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"
```

- Verifica GET /health cada 30 segundos
- Timeout 10s
- Espera 5s antes de empezar (start-period)
- Reintentar 3 veces antes de marcar como unhealthy

ECS también configurará target group health check en ALB.

## Building the Image

### Prerequisites

```bash
# Ensure Docker is installed
docker --version

# Ensure you're in the service directory
cd services/timeline-service
```

### Build Image (Local)

```bash
# Build with tag
docker build -t timeline-service:dev .

# Build and push to ECR
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
ECR_REPO=cloud-incident-timeline/timeline-service

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:dev .

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:dev
```

### Build Output

```
Step 1/15 : FROM python:3.11-slim as builder
Step 2/15 : WORKDIR /app
...
Step 15/15 : ENTRYPOINT ["./entrypoint.sh"]
Successfully built abc123def456
Successfully tagged timeline-service:dev
```

## Testing Image Locally

### Docker Compose (Recommended)

```bash
# Set AWS credentials in environment or .env
export AWS_REGION=us-east-1
export TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline
export TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../queue

# Start container via docker-compose
docker-compose up

# Output:
# timeline-service-dev | ==========================================
# timeline-service-dev | Timeline Service Starting Up
# timeline-service-dev | Service: timeline-service
# timeline-service-dev | Port: 8080
# timeline-service-dev | Log Level: DEBUG
# timeline-service-dev |
# timeline-service-dev | Starting FastAPI HTTP server on port 8080...
# timeline-service-dev | FastAPI started (PID 45)
# timeline-service-dev |
# timeline-service-dev | Starting SQS Consumer...
# timeline-service-dev | SQS Consumer started (PID 89)
```

**In another terminal, test endpoints:**

```bash
# Health check
curl http://localhost:8002/health
# {"status":"ok","service":"timeline-service"}

# Get timeline
curl http://localhost:8002/incidents/inc-001/timeline
# {"incident_id":"inc-001","entries":[]}

# Add comment
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"comment":"Test comment","user_id":"user-1"}'
# {"timeline_entry_id":"tl-001",...}
```

**Shutdown:**

```bash
# Graceful shutdown
docker-compose down

# Output:
# timeline-service-dev | Received shutdown signal, gracefully stopping services...
# timeline-service-dev | Stopping FastAPI (PID 45)...
# timeline-service-dev | FastAPI stopped
# timeline-service-dev | Stopping SQS Consumer (PID 89)...
# timeline-service-dev | SQS Consumer stopped
# timeline-service-dev | ==========================================
# timeline-service-dev | Timeline Service Shutdown Complete
# timeline-service-dev | ==========================================
```

### Standalone Docker Run

```bash
# Run container directly
docker run -d \
  --name timeline-service \
  -p 8002:8080 \
  -e AWS_REGION=us-east-1 \
  -e TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline \
  -e TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../queue \
  timeline-service:dev

# View logs
docker logs -f timeline-service

# Test
curl http://localhost:8002/health

# Stop
docker stop timeline-service
docker rm timeline-service
```

## Deployment to ECS/Fargate

### Prerequisites

1. ECR Repository created (via Terraform Phase 1)
2. ECS Cluster created (via Terraform Phase 1)
3. Docker image pushed to ECR

### Workflow

```bash
# 1. Build image
docker build -t timeline-service:dev .

# 2. Tag with ECR repository URL
docker tag timeline-service:dev \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cloud-incident-timeline/timeline-service:dev

# 3. Push to ECR
docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cloud-incident-timeline/timeline-service:dev

# 4. Create/Update ECS Task Definition (via Terraform Phase 2)
terraform apply -target=module.timeline_task_definition

# 5. Create/Update ECS Service (via Terraform Phase 2)
terraform apply -target=aws_ecs_service.timeline

# 6. Validate
# → ECS tasks pull image from ECR
# → Tasks start and run entrypoint.sh
# → FastAPI listens on 8080
# → ALB health check: GET /health → 200 OK
# → ALB forwards requests to target group
```

### ECS Task Definition (Terraform)

Example from `infrastructure/modules/ecs-service/`:

```hcl
container_definitions = jsonencode([{
  name      = "timeline-service"
  image     = "${var.ecr_repository_url}:${var.image_tag}"  # ECR image URL + dev tag
  
  portMappings = [{
    containerPort = 8080
    hostPort      = 8080
    protocol      = "tcp"
  }]
  
  environment = [
    { name = "AWS_REGION", value = var.aws_region }
    { name = "TIMELINE_TABLE_NAME", value = var.timeline_table_name }
    { name = "TIMELINE_QUEUE_URL", value = var.timeline_queue_url }
    { name = "SERVICE_NAME", value = "timeline-service" }
    { name = "LOG_LEVEL", value = "INFO" }
    { name = "PORT", value = "8080" }
  ]
  
  logConfiguration = {
    logDriver = "awslogs"
    options = {
      awslogs-group         = "/ecs/timeline-service"
      awslogs-region        = var.aws_region
      awslogs-stream-prefix = "ecs"
    }
  }
  
  healthCheck = {
    command     = ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
    interval    = 30
    timeout     = 10
    retries     = 3
    startPeriod = 5
  }
}])
```

### Target Group Health Check (Terraform)

```hcl
health_check {
  healthy_threshold   = 2
  unhealthy_threshold = 2
  timeout             = 10
  interval            = 30
  path                = "/health"
  matcher             = "200"
}
```

### Container Resources (Terraform)

```hcl
cpu    = 256  # 0.25 vCPU
memory = 512  # 512 MB

# Per ECS Fargate spec: CPU/memory combinations
# Valid combinations: (256, 512/1024/2048), (512, 1024-4096), etc.
```

## Environment Variables

**Required in ECS Task:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `AWS_REGION` | `us-east-1` | AWS region |
| `TIMELINE_TABLE_NAME` | `cloud-incident-timeline-dev-incident-timeline` | DynamoDB table |
| `TIMELINE_QUEUE_URL` | Full SQS queue URL | SQS queue |
| `SERVICE_NAME` | `timeline-service` | Service ID |
| `LOG_LEVEL` | `INFO` | Log level |
| `PORT` | `8080` | Container port |

**Omitted from ECS (use defaults or .env in development):**

| Variable | Default | When Used |
|----------|---------|-----------|
| `EVENT_BUS_NAME` | `default` | EventBridge (optional) |

**Note:** AWS credentials are provided via ECS Task Role IAM policy, not environment variables.

## Logging

All output from both processes goes to:

1. **Container stdout** → Docker daemon → ECS agent → CloudWatch Logs
2. **JSON structured logs** from Python application

**Viewing logs in ECS:**

```bash
# CloudWatch Logs group: /ecs/timeline-service
aws logs tail /ecs/timeline-service --follow

# Output:
# 2026-09-03T12:30:45Z timeline-service Timeline Service Starting Up
# 2026-09-03T12:30:45Z timeline-service Starting FastAPI HTTP server on port 8080...
# 2026-09-03T12:30:46Z uvicorn[45] Uvicorn running on http://0.0.0.0:8080
# 2026-09-03T12:30:47Z timeline-service Starting SQS Consumer...
# 2026-09-03T12:30:48Z src.services.sqs_consumer SQS Consumer starting up
# 2026-09-03T12:30:48Z timeline-service SQS Consumer started (PID 89)
```

## Performance & Optimization

### Image Size

```
Multi-stage build reduces image from:
  - Without optimization: ~500MB (includes build tools)
  - With multi-stage: ~200MB (only runtime)

Savings: ~60% reduction = faster ECR pull time in ECS
```

### Resource Usage

**Per ECS Specification:**

```
CPU:    256 (0.25 vCPU)
Memory: 512 MB

Both processes fit comfortably:
  - FastAPI: ~100-150 MB
  - SQS Consumer: ~80-100 MB
  - OS/Python runtime: ~150-200 MB
```

### Graceful Shutdown

**ECS sends SIGTERM → Container has time to clean up:**

```
Timeline:
  t=0s: ECS sends SIGTERM to container
  t=0s: Entrypoint catches SIGTERM
  t=0s-2s: FastAPI completes current request
  t=0s-2s: SQS Consumer finishes processing message
  t=2s: Both processes exit
  t=30s: ECS forcibly kills container if still running (SIGKILL)

Result: Graceful shutdown without data loss
```

## Troubleshooting

### Image Build Fails

```
Error: "pip install -r requirements.txt" fails

Solution:
  1. Check Python version (3.11+)
  2. Check requirements.txt syntax
  3. Check for network issues
  4. Use --no-cache: docker build --no-cache -t timeline-service:dev .
```

### Container Fails to Start

```
Error: "entrypoint.sh: command not found"

Solution:
  1. Verify entrypoint.sh has execute permission: chmod +x entrypoint.sh
  2. Verify Dockerfile: RUN chmod +x entrypoint.sh
  3. Check line endings (Windows CRLF vs Unix LF)
     dos2unix entrypoint.sh  # Or in Dockerfile: RUN dos2unix /app/entrypoint.sh
```

### Health Check Fails

```
Error: "container unhealthy"

Solution:
  1. Test manually: docker exec <container> curl http://localhost:8080/health
  2. Check FastAPI is running: docker logs <container> | grep "Uvicorn running"
  3. Check port: docker port <container>
  4. Increase health check start period: startPeriod = 10 (in Task Definition)
```

### SQS Consumer Not Running

```
Error: "SQS Consumer stopped unexpectedly"

Solution:
  1. Check logs: docker logs <container> | grep "SQS Consumer"
  2. Verify TIMELINE_QUEUE_URL is set: docker inspect <container>
  3. Verify AWS IAM permissions for SQS
  4. Verify queue exists in AWS
```

## Next Steps

- **Phase 7:** Complete documentation and deployment validation
- Register image with ECR
- Deploy via Terraform ECS module
- Validate with ALB health checks

## Files Created

```
services/timeline-service/
├── Dockerfile              ← Multi-stage build
├── entrypoint.sh           ← Process orchestration
├── docker-compose.yml      ← Local testing
├── .dockerignore           ← (Already exists)
└── PHASE_6_DOCKERIZATION.md ← This file
```

## Summary

**Fase 6 implementa:**

✅ Multi-stage Docker build (200MB image)
✅ Concurrent process orchestration (FastAPI + Consumer)
✅ Graceful shutdown handling (SIGTERM, SIGINT)
✅ Health check integration (ALB compatible)
✅ Local testing via docker-compose
✅ ECS/Fargate deployment ready
✅ CloudWatch Logs integration
✅ Resource-optimized for Fargate (256 CPU / 512 MB)

**Próximo:** Fase 7 - Complete documentation & deployment validation
