# Timeline Service

Event-driven microservice for managing incident timelines. Consumes events from SQS queue and exposes HTTP API for timeline queries and comment management.

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

### Manual Testing

#### Health Check
```bash
curl http://localhost:8002/health
```

**Response (200):**
```json
{
  "status": "ok",
  "service": "timeline-service"
}
```

#### Get Timeline
```bash
curl http://localhost:8002/incidents/inc-001/timeline
```

**Response (200):**
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

#### Add Comment
```bash
curl -X POST http://localhost:8002/incidents/inc-001/timeline/comments \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Database team investigating performance issue",
    "user_id": "user-123"
  }'
```

**Response (201):**
```json
{
  "timeline_entry_id": "tl-003",
  "incident_id": "inc-001",
  "message": "Comment: Database team investigating performance issue",
  "created_at": "2026-09-02T12:45:30Z"
}
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

## Deployment

### Docker

```bash
# Build image
docker build -t timeline-service:latest .

# Run container
docker run -p 8002:80 \
  -e AWS_REGION=us-east-1 \
  -e TIMELINE_TABLE_NAME=cloud-incident-timeline-dev-incident-timeline \
  -e TIMELINE_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../queue \
  timeline-service:latest
```

### ECS/Fargate

The Dockerfile sets up both FastAPI HTTP server and SQS consumer in one container:

```dockerfile
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 80 & python -m src.consumer"]
```

ALB configuration:
- **Target Group:** Port 80, path `/incidents*`
- **Health Check:** GET /health, expect 200

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
