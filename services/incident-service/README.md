# Incident Service

HTTP API for incident management. Handles the lifecycle and current state of incidents.

## Tech Stack

- **Runtime**: Python 3.11+
- **Framework**: FastAPI
- **AWS SDK**: boto3
- **Database**: DynamoDB
- **Event Bus**: EventBridge
- **Logging**: Structured JSON

## Directory Structure

```
incident-service/
├── src/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration from environment variables
│   ├── constants.py         # Shared constants and enumerations
│   ├── schemas.py           # Pydantic models for requests/responses
│   ├── logger.py            # Structured logging configuration
│   ├── context.py           # Correlation ID handling
│   ├── utils.py             # Utilities and validation
│   ├── models/
│   │   ├── __init__.py
│   │   └── incident.py      # Incident domain model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── incident_service.py    # Incident business logic
│   │   └── event_publisher.py     # Event publishing
│   └── routes/
│       ├── __init__.py
│       └── incidents.py           # Incident API endpoints
├── Dockerfile               # Docker image
├── .dockerignore            # Files to ignore in build
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
└── README.md                # This documentation
```

## Environment Variables

**Required:**

```bash
AWS_REGION=eu-west-3
INCIDENTS_TABLE_NAME=cloud-incident-timeline-dev-incidents
EVENT_BUS_NAME=cloud-incident-timeline-dev-event-bus
```

**Optional:**

```bash
SERVICE_NAME=incident-service
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
HOST=0.0.0.0
PORT=8001
```

See `.env.example` for a complete template.

## Local Development

### Requirements

- Python 3.11+
- pip or poetry

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run locally

```bash
# Development mode (with auto-reload)
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001

# Production mode
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

Access at: `http://localhost:8001`

Interactive documentation: `http://localhost:8001/docs`

### Health check

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "incident-service"
}
```

## Phase 2: HTTP API Endpoints

All endpoints return consistent error responses and include Correlation ID.

### Create Incident

```bash
curl -X POST http://localhost:8001/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API latency spike",
    "description": "The public API is responding slowly",
    "severity": "HIGH",
    "actor": {
      "user_id": "user-001",
      "email": "user@example.com"
    }
  }'
```

Response (201 Created):
```json
{
  "incident_id": "inc-a1b2c3d4e5f6",
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "HIGH",
  "status": "OPEN",
  "created_at": "2026-08-11T10:30:00Z",
  "updated_at": "2026-08-11T10:30:00Z"
}
```

### List Incidents

```bash
curl http://localhost:8001/incidents
```

Response (200 OK):
```json
{
  "items": [
    {
      "incident_id": "inc-a1b2c3d4e5f6",
      "title": "API latency spike",
      "description": "The public API is responding slowly",
      "severity": "HIGH",
      "status": "OPEN",
      "created_at": "2026-08-11T10:30:00Z",
      "updated_at": "2026-08-11T10:30:00Z"
    }
  ]
}
```

### Get Incident by ID

```bash
curl http://localhost:8001/incidents/inc-a1b2c3d4e5f6
```

Response (200 OK):
```json
{
  "incident_id": "inc-a1b2c3d4e5f6",
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "HIGH",
  "status": "OPEN",
  "created_at": "2026-08-11T10:30:00Z",
  "updated_at": "2026-08-11T10:30:00Z"
}
```

### Update Incident Status

```bash
curl -X PATCH http://localhost:8001/incidents/inc-a1b2c3d4e5f6/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "INVESTIGATING",
    "actor": {
      "user_id": "user-001",
      "email": "user@example.com"
    }
  }'
```

Response (200 OK):
```json
{
  "incident_id": "inc-a1b2c3d4e5f6",
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "HIGH",
  "status": "INVESTIGATING",
  "created_at": "2026-08-11T10:30:00Z",
  "updated_at": "2026-08-11T10:35:00Z"
}
```

### Update Incident Severity

```bash
curl -X PATCH http://localhost:8001/incidents/inc-a1b2c3d4e5f6/severity \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "CRITICAL",
    "actor": {
      "user_id": "user-001",
      "email": "user@example.com"
    }
  }'
```

Response (200 OK):
```json
{
  "incident_id": "inc-a1b2c3d4e5f6",
  "title": "API latency spike",
  "description": "The public API is responding slowly",
  "severity": "CRITICAL",
  "status": "INVESTIGATING",
  "created_at": "2026-08-11T10:30:00Z",
  "updated_at": "2026-08-11T10:40:00Z"
}
```

### Error Response Example

```bash
curl -X POST http://localhost:8001/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "description": "Test",
    "severity": "INVALID"
  }'
```

Response (400 Bad Request):
```json
{
  "message": "Validation error",
  "details": [
    {
      "field": "severity",
      "message": "Invalid severity. Must be one of: LOW, MEDIUM, HIGH, CRITICAL"
    }
  ]
}
```

## Docker

### Build

```bash
docker build -t incident-service:dev .
```

### Run

```bash
docker run -p 8001:8001 \
  -e AWS_REGION=eu-west-3 \
  -e INCIDENTS_TABLE_NAME=cloud-incident-timeline-dev-incidents \
  -e EVENT_BUS_NAME=cloud-incident-timeline-dev-event-bus \
  incident-service:dev
```

## Phase 1 Implemented Conventions

### ✅ Event Envelope

All events published to EventBridge follow this structure:

```json
{
  "version": "1.0",
  "event_id": "evt-001",
  "event_type": "IncidentCreated",
  "source": "incident-service",
  "occurred_at": "2026-07-30T08:00:00Z",
  "correlation_id": "corr-001",
  "actor": {
    "user_id": "user-001",
    "email": "user@example.com"
  },
  "data": {}
}
```

### ✅ Correlation ID

- Auto-generated by middleware if not in headers
- Searched in header `X-Correlation-ID`
- Included in responses
- Logged in all logs

### ✅ Structured Logging

All logs emitted in JSON format with fields:

```json
{
  "timestamp": "2026-07-30T08:00:00Z",
  "level": "INFO",
  "service": "incident-service",
  "message": "Incident created",
  "correlation_id": "corr-001",
  "incident_id": "inc-001"
}
```

### ✅ Error Responses

Standard format for errors:

```json
{
  "message": "Validation error",
  "details": [
    {
      "field": "severity",
      "message": "Must be one of: LOW, MEDIUM, HIGH, CRITICAL"
    }
  ]
}
```

### ✅ Validations

Valid statuses:
- `OPEN`
- `INVESTIGATING`
- `RESOLVED`
- `CLOSED`

Valid severities:
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

## Phase 2 Implementation

### ✅ HTTP Endpoints Implemented

- ✅ `GET /health` - Health check for ALB/ECS
- ✅ `POST /incidents` - Create new incident, publishes IncidentCreated event
- ✅ `GET /incidents` - List all incidents
- ✅ `GET /incidents/{incident_id}` - Get incident by ID
- ✅ `PATCH /incidents/{incident_id}/status` - Update status, publishes IncidentStatusChanged or IncidentResolved
- ✅ `PATCH /incidents/{incident_id}/severity` - Update severity, publishes IncidentSeverityChanged

### ✅ Core Components

- **models/incident.py**: Domain model with validation
- **services/incident_service.py**: Business logic (in-memory storage, will be DynamoDB in Phase 3)
- **services/event_publisher.py**: Event publishing (logging stubs, will be EventBridge in Phase 4)
- **routes/incidents.py**: FastAPI endpoints with full error handling

### ✅ Features

- Request validation with detailed error responses
- Event publishing on state changes
- Correlation ID propagation in all logs
- Structured JSON logging
- Complete HTTP error handling
- Interactive API documentation at `/docs`

### Current Limitations (To Be Addressed)

- **Phase 3**: Replace in-memory storage with DynamoDB
- **Phase 4**: Replace event logging with actual EventBridge integration
- **Phase 5**: Add timeline and audit consumer routing

## Testing

```bash
# Run tests
python -m pytest

# With coverage
python -m pytest --cov=src
```

## Next Phases

- **Phase 3**: DynamoDB integration (replace in-memory storage)
- **Phase 4**: EventBridge publishing (replace event logging)
- **Phase 5**: E2E verification with consumers

## References

- [Service specifications](../services-implementation-specs.md)
- [Services implementation guide](../.instructions.md)
- [Global instructions](../../.github/copilot-instructions.md)
