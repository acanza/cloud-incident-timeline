# Timeline Service

**Version:** 0.1.0  
**Status:** ✅ Production Ready (MVP)

Event-driven microservice for managing incident timelines. Consumes events from SQS queue and exposes HTTP API for timeline queries and comment management.

**Architecture:** Concurrent FastAPI HTTP server + SQS Consumer in single Docker container  
**Database:** DynamoDB (incident_timeline table)  
**Message Queue:** SQS + EventBridge  
**Deployment:** ECS/Fargate (256 CPU / 512 MB)

## Architecture

```
Timeline Service Components:
├─ HTTP API (FastAPI)
│  ├─ GET /health - ALB health checks
│  ├─ GET /incidents/{incident_id}/timeline - Query timeline
│  └─ POST /incidents/{incident_id}/timeline/comments - Add comment
│
└─ SQS Consumer (Background)
   └─ Long polls queue, processes events, writes to DynamoDB
```

## Quick Start

### Prerequisites

- Python 3.9+
- AWS credentials configured (via environment, IAM role, or `.env`)
- DynamoDB table: `cloud-incident-timeline-dev-incident-timeline`
- SQS queue: `cloud-incident-timeline-dev-timeline-queue`

### Setup

```bash
cd services/timeline-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS settings:
#   AWS_REGION=us-east-1
#   TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline
#   TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../timeline-queue
```

### Run Service

```bash
# Terminal 1: Start FastAPI HTTP server
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8002

# Terminal 2: Start SQS consumer (in separate terminal)
python3 -c "from src.services.sqs_consumer import SQSConsumer; SQSConsumer().start()"
```

**Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     Started server process [1234]
...
```

Visit:
- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc
- **Health Check:** http://localhost:8002/health

---

## Testing Endpoints

### Automated Test Script

```bash
# Make script executable (first time only)
chmod +x test-endpoints.sh

# Run tests
./test-endpoints.sh
```

This script tests:
1. ✅ Health check
2. ✅ Get empty timeline
3. ✅ Add comments
4. ✅ Get timeline with entries
5. ✅ Validation errors (missing/empty/long comments)
6. ✅ Invalid incident_id format

**Example output:**
```
================================================
Testing Timeline Service API
================================================

1. Health check...
{
  "status": "ok",
  "service": "timeline-service"
}

2. Getting timeline for incident (initially empty)...
{
  "incident_id": "inc-test-001",
  "entries": []
}

3. Adding first comment...
{
  "timeline_entry_id": "tl-001",
  "incident_id": "inc-test-001",
  "message": "Comment: Backend team is investigating database metrics",
  "created_at": "2026-09-02T12:30:45Z"
}

...
```

## Testing Endpoints

### Automated Test Script

```bash
# Make script executable (first time only)
chmod +x test-endpoints.sh

# Run tests
./test-endpoints.sh
```

This script tests:
1. ✅ Health check
2. ✅ Get empty timeline
3. ✅ Add comments
4. ✅ Get timeline with entries
5. ✅ Validation errors (missing/empty/long comments)
6. ✅ Invalid incident_id format

**Example output:**
```
================================================
Testing Timeline Service API
================================================

1. Health check...
{
  "status": "ok",
  "service": "timeline-service"
}
...
```

### Docker Compose Testing (Recommended)

```bash
cd services/timeline-service

# Build image
docker build -t timeline-service:dev .

# Start service (FastAPI only, no SQS Consumer)
docker-compose up

# In another terminal, run tests
./test-endpoints.sh

# Stop service
docker-compose down
```

**Expected output:**
```
timeline-service-dev | ==========================================
timeline-service-dev | Timeline Service Ready
timeline-service-dev | ==========================================
timeline-service-dev | HTTP API: http://localhost:8080
timeline-service-dev | Health Check: http://localhost:8080/health
timeline-service-dev | Swagger: http://localhost:8080/docs
timeline-service-dev |
timeline-service-dev | Processes running:
timeline-service-dev |   - FastAPI (PID 45)
```

### Manual API Testing

#### Health Check
```bash
curl http://localhost:8002/health

# Response:
{"status":"ok","service":"timeline-service"}
```

#### Get Timeline
```bash
curl http://localhost:8002/incidents/inc-001/timeline

# Response:
{
  "incident_id": "inc-001",
  "entries": []
}
```

#### Add Comment
```bash
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Database team investigating performance issue",
    "user_id": "user-123"
  }'

# Response (201):
{
  "timeline_entry_id": "tl-001",
  "incident_id": "inc-001",
  "message": "Comment: Database team investigating performance issue",
  "created_at": "2026-09-04T10:30:45Z"
}
```

#### Add Multiple Comments & Query
```bash
# Add comment 1
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"comment":"Issue detected","user_id":"user-1"}'

# Add comment 2
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"comment":"Root cause identified","user_id":"user-2"}'

# Get timeline (should have 2 entries)
curl http://localhost:8002/incidents/inc-001/timeline
```

#### Test Validation Errors
```bash
# Missing comment
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-1"}'
# → 400 Bad Request

# Empty comment
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"comment":"","user_id":"user-1"}'
# → 400 Bad Request

# Comment > 1000 chars (invalid)
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{"comment":"'$(printf 'A%.0s' {1..1001})'","user_id":"user-1"}'
# → 400 Bad Request
```

---

## API Endpoints

### GET /health

Health check endpoint for ALB and monitoring.

```
Status: 200 OK
Headers: Content-Type: application/json
Body: {"status": "ok", "service": "timeline-service"}
```

**Use Cases:**
- ALB target group health checks
- Kubernetes/ECS readiness probes
- Service availability monitoring

---

### GET /incidents/{incident_id}/timeline

Retrieve the timeline for a specific incident.

```
Method: GET
Path: /incidents/{incident_id}/timeline
Status: 200 OK
```

**Response:**
```json
{
  "incident_id": "inc-001",
  "entries": [
    {
      "incident_id": "inc-001",
      "timeline_entry_id": "tl-001",
      "created_at": "2026-07-30T08:00:00Z",
      "message": "Incident created with HIGH severity and OPEN status.",
      "event_type": "IncidentCreated",
      "source_event_id": "evt-001"
    }
  ]
}
```

**Errors:**
- `400` - Invalid incident_id
- `500` - Database error

---

### POST /incidents/{incident_id}/timeline/comments

Add a comment to an incident's timeline.

```
Method: POST
Path: /incidents/{incident_id}/timeline/comments
Status: 201 Created
```

**Request Body:**
```json
{
  "comment": "String, required, max 1000 chars",
  "user_id": "String, optional"
}
```

**Response (201):**
```json
{
  "timeline_entry_id": "tl-003",
  "incident_id": "inc-001",
  "message": "Comment: Database team investigating issue",
  "created_at": "2026-09-02T12:45:30Z"
}
```

**Errors:**
- `400` - Missing/empty comment or comment > 1000 chars
- `500` - Database error

---

## Project Structure

```
timeline-service/
├── src/
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Configuration & env vars
│   ├── context.py                   # AWS clients singleton
│   ├── logger.py                    # Structured JSON logging
│   ├── constants.py                 # Domain constants
│   ├── schemas.py                   # Pydantic models for HTTP
│   ├── exceptions.py                # Custom exceptions
│   ├── http_responses.py            # HTTP response helpers
│   ├── utils.py                     # Utility functions
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py                # GET /health endpoint
│   │   └── timeline.py              # GET/POST timeline endpoints
│   │
│   ├── models/
│   │   ├── timeline.py              # TimelineEntry data model
│   │   ├── event.py                 # Event models (domain)
│   │   ├── validators.py            # Event & entry validation
│   │   └── transformer.py           # Event → message transformation
│   │
│   └── services/
│       ├── timeline_service.py      # Business logic orchestrator
│       ├── timeline_repository.py   # DynamoDB access layer
│       ├── message_handler.py       # SQS message processor
│       └── sqs_consumer.py          # SQS polling loop
│
├── test-endpoints.sh                # Bash test script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── .dockerignore                    # Docker build ignore
│
├── PHASE_3_DYNAMODB.md             # Phase 3 documentation
├── PHASE_4_SQS_CONSUMER.md         # Phase 4 documentation
├── PHASE_5_HTTP_API.md             # Phase 5 documentation
└── README.md                        # This file
```

---

## Configuration

All configuration via environment variables (see `.env.example`):

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `AWS_REGION` | Yes | `us-east-1` | AWS region |
| `TIMELINE_TABLE_NAME` | Yes | `cloud-incident-timeline-dev-incident-timeline` | DynamoDB table |
| `TIMELINE_QUEUE_URL` | Yes | `https://sqs.us-east-1.amazonaws.com/.../queue` | SQS queue |
| `EVENT_BUS_NAME` | No | `default` | EventBridge event bus |
| `SERVICE_NAME` | No | `timeline-service` | Service identifier |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `PORT` | No | `80` | HTTP server port |

**Local Development (.env):**
```bash
AWS_REGION=us-east-1
TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline
TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/cloud-incident-timeline-dev-timeline-queue
EVENT_BUS_NAME=default
SERVICE_NAME=timeline-service
LOG_LEVEL=DEBUG
PORT=8002
```

---

## Event Types (Consumed from SQS)

Timeline service consumes these events from the queue:

| Event Type | Source | Action |
|-----------|--------|--------|
| `IncidentCreated` | incident-service | Timeline: "Incident created with {severity} and {status}" |
| `IncidentStatusChanged` | incident-service | Timeline: "Status changed from {prev} to {new}" |
| `IncidentSeverityChanged` | incident-service | Timeline: "Severity changed from {prev} to {new}" |
| `IncidentResolved` | incident-service | Timeline: "Incident resolved. Resolution: {summary}" |
| `TimelineCommentAdded` | incident-service | Timeline: "Comment: {text}" |

Each event includes:
- `event_id`: Unique event identifier
- `incident_id`: Associated incident ID
- `source_event_id`: For idempotency (prevents duplicates on SQS retries)
- `correlation_id`: For distributed tracing
- `occurred_at`: Event timestamp (ISO format)

---

## Docker Deployment

### Image Details

**Multi-stage Build:**
- **Stage 1 (Builder):** Python 3.11 + build tools + pip install
- **Stage 2 (Runtime):** Python 3.11-slim + dependencies + code
- **Final Size:** ~200 MB (60% reduction from single-stage)
- **Base Image:** `python:3.11-slim`

**Optimization:**
- ✅ Multi-stage reduces image size
- ✅ Reduces ECR storage costs
- ✅ Faster ECS task startup
- ✅ Non-privileged port (8080)

### Build Image

```bash
cd services/timeline-service

# Build locally
docker build -t timeline-service:dev .

# Build for ECR
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
ECR_URL=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cloud-incident-timeline/timeline-service

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and tag
docker build -t $ECR_URL:dev .

# Push to ECR
docker push $ECR_URL:dev
```

### Run Locally with Docker

**Option 1: Docker Compose (Recommended)**

```bash
# Start service
docker-compose up

# In another terminal, test
curl http://localhost:8002/health

# Stop
docker-compose down
```

**Option 2: Docker Run**

```bash
docker run -d \
  --name timeline-service \
  -p 8002:8080 \
  -e AWS_REGION=us-east-1 \
  -e TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline \
  -e TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../queue \
  -e START_CONSUMER=false \
  timeline-service:dev

# View logs
docker logs -f timeline-service

# Stop
docker stop timeline-service
docker rm timeline-service
```

### Environment Variables

**For Local Testing (docker-compose):**

```yaml
# .env
AWS_REGION=us-east-1
TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline
TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/queue
SERVICE_NAME=timeline-service
LOG_LEVEL=DEBUG
PORT=8080
START_CONSUMER=false
```

**For ECS/Fargate:**

```hcl
# Terraform task definition
environment = [
  { name = "AWS_REGION", value = "us-east-1" }
  { name = "TIMELINE_TABLE_NAME", value = "cloud-incident-timeline-dev-incident-timeline" }
  { name = "TIMELINE_QUEUE_URL", value = "https://sqs.us-east-1.amazonaws.com/.../queue" }
  { name = "SERVICE_NAME", value = "timeline-service" }
  { name = "LOG_LEVEL", value = "INFO" }
  { name = "PORT", value = "8080" }
  { name = "START_CONSUMER", value = "true" }
]
```

**Notes:**
- `START_CONSUMER=false` for local testing (no AWS credentials)
- `START_CONSUMER=true` for production (ECS Task Role provides credentials)
- AWS credentials in ECS via IAM Task Role, not environment

### Entrypoint Orchestration

Container runs `entrypoint.sh` which:

1. Validates configuration
2. Starts FastAPI HTTP server (port 8080)
3. Starts SQS Consumer (optional, if `START_CONSUMER=true`)
4. Registers signal handlers for graceful shutdown
5. Waits for both processes

**Graceful Shutdown Flow:**

```
ECS SIGTERM → Entrypoint → Kill FastAPI → Kill Consumer → Exit
  ↓                          ↓
  t=0s                    t=0-2s (complete current work)
  ↓                          ↓
  t=30s (SIGKILL if not done)  t=2-5s exit
```

### Health Checks

**Docker HEALTHCHECK (every 30s):**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"
```

**ALB Target Group Health Check:**

```
Path: /health
Protocol: HTTP
Port: 8080
Interval: 30s
Timeout: 10s
Healthy Threshold: 2
Unhealthy Threshold: 2
```

### ECS/Fargate Deployment

**Workflow:**

1. Build and push image to ECR
2. Create/update ECS Task Definition
3. Create/update ECS Service
4. ALB forwards traffic
5. Tasks pass health checks

**Task Definition (Terraform):**

```hcl
module "timeline_task" {
  source = "./modules/ecs-service"
  
  name              = "timeline-service"
  image_uri         = "${aws_ecr_repository.timeline.repository_url}:dev"
  container_port    = 8080
  cpu               = 256
  memory            = 512
  desired_count     = 1
  
  environment = [
    { name = "TIMELINE_TABLE_NAME", value = var.timeline_table_name }
    { name = "TIMELINE_QUEUE_URL", value = aws_sqs_queue.timeline.url }
    { name = "START_CONSUMER", value = "true" }
  ]
  
  iam_task_role_arn = aws_iam_role.timeline_task.arn
}
```

**ALB Listener Rule:**

```hcl
resource "aws_lb_listener_rule" "timeline" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.timeline.arn
  }
  
  condition {
    path_pattern {
      values = ["/incidents/*/timeline*"]
    }
  }
}
```

---

## Logging

Structured JSON logging with context fields:

```json
{
  "timestamp": "2026-09-02T12:30:45.123Z",
  "level": "INFO",
  "logger": "src.services.timeline_service",
  "message": "Timeline entry created",
  "incident_id": "inc-001",
  "timeline_entry_id": "tl-003",
  "event_type": "IncidentCreated",
  "correlation_id": "corr-001"
}
```

This enables:
- Correlation tracing across services (via `correlation_id`)
- Incident-scoped debugging
- Structured log queries (CloudWatch Insights, etc.)

---

## Troubleshooting

### Service won't start

```
❌ ERROR: Service is not responding at http://localhost:8002
```

**Check:**
1. Is server running? `ps aux | grep uvicorn`
2. Is port 8002 available? `lsof -i :8002`
3. Are dependencies installed? `pip list | grep fastapi`

**Fix:**
```bash
# Kill any running instance
lsof -i :8002 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Start fresh
python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8002
```

### "Table not found" error

```
❌ ResourceNotFoundException: Requested resource not found
```

**Check .env:**
```bash
echo $TIMELINE_TABLE_NAME
# Should match actual DynamoDB table name
```

**Fix:**
1. Verify DynamoDB table exists in AWS console
2. Verify table name in `.env` is correct
3. Verify AWS credentials have DynamoDB access

### "Queue not found" error

```
❌ QueueDoesNotExist
```

**Check .env:**
```bash
echo $TIMELINE_QUEUE_URL
# Should match actual SQS queue URL
```

**Fix:**
1. Verify SQS queue exists in AWS console
2. Verify queue URL in `.env` is correct (full URL, not just name)
3. Verify AWS credentials have SQS access

---

## Performance

Long polling configuration (optimized):
- `MaxNumberOfMessages`: 10 (batch processing)
- `WaitTimeSeconds`: 20 (reduces API calls & latency)
- `VisibilityTimeout`: 300s (5 minutes for processing)

This means:
- Poll every 20 seconds (not 1 second)
- Process up to 10 messages per poll
- Cost: ~2,592 API calls/day (vs 86,400 with 1s polling)

---

## Development

### Run Tests

```bash
# Automated endpoint testing
./test-endpoints.sh

# Manual testing with curl
curl http://localhost:8002/health
curl http://localhost:8002/incidents/inc-001/timeline
```

### Code Style

```bash
# Format (black)
black src/ --line-length 100

# Lint (pylint)
pylint src/

# Type check (mypy)
mypy src/ --ignore-missing-imports
```

---

## Next Steps

- **Phase 6:** Dockerization & multi-process orchestration
- **Phase 7:** Complete documentation & deployment

---

## License

Proprietary - Cloud Incident Timeline Project
