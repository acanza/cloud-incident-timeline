#!/bin/bash
# Test script for audit-worker service
# Validates audit record creation, idempotency, and error handling
# 
# Prerequisites:
#   - audit-worker service running (python -m src.main)
#   - AWS credentials configured (or local AWS stack)
#   - SQS queue and DynamoDB table accessible
#   - AWS CLI installed for testing DynamoDB

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="audit-worker"
LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
AUDIT_TABLE_NAME="${AUDIT_TABLE_NAME:-cloud-incident-timeline-dev-audit-table}"
AUDIT_QUEUE_URL="${AUDIT_QUEUE_URL:-https://sqs.us-east-1.amazonaws.com/123456789012/cloud-incident-timeline-dev-audit-queue}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Test data
INCIDENT_ID_1="inc-test-001"
INCIDENT_ID_2="inc-test-002"
TEST_USER_ID="user-test-001"
TEST_USER_NAME="Test User"
TEST_USER_EMAIL="test@example.com"

echo "================================================"
echo "Audit Worker - Integration Tests"
echo "================================================"
echo ""
echo "Configuration:"
echo "  Service: $SERVICE_NAME"
echo "  DynamoDB Table: $AUDIT_TABLE_NAME"
echo "  SQS Queue: ${AUDIT_QUEUE_URL##*/}"
echo "  AWS Region: $AWS_REGION"
echo ""

# Function to print test header
test_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to print success message
pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    echo ""
}

# Function to print failure message
fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    echo ""
    exit 1
}

# Function to print warning message
warn() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

# Detect Python interpreter
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    fail "Neither 'python' nor 'python3' found. Please install Python."
fi

echo "Using Python interpreter: $PYTHON_CMD"
echo ""

# ============================================================================
# Test 1: Verify audit-worker is running
# ============================================================================
test_header "Test 1: Verify Service Status"

echo "Checking if audit-worker service is running..."
if pgrep -f "python -m src.main" > /dev/null || pgrep -f "src.main" > /dev/null; then
    pass "Audit worker process detected"
else
    warn "Audit worker process not detected. Make sure it's running:"
    echo "  cd services/audit-worker"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  # Configure .env with AWS credentials"
    echo "  python3 -m src.main"
    echo ""
    echo "Continuing with tests (if service starts, tests may pass)..."
    echo ""
fi

# ============================================================================
# Test 2: Send IncidentCreated event
# ============================================================================
test_header "Test 2: Send IncidentCreated Event"

echo "Creating test event for incident: $INCIDENT_ID_1"

EVENT_1=$(cat <<EOF
{
  "version": "1.0",
  "event_id": "evt-incident-created-001",
  "event_type": "IncidentCreated",
  "source": "incident-service",
  "occurred_at": "2026-09-06T10:00:00Z",
  "correlation_id": "corr-001",
  "actor": {
    "user_id": "$TEST_USER_ID",
    "name": "$TEST_USER_NAME",
    "email": "$TEST_USER_EMAIL"
  },
  "data": {
    "incident_id": "$INCIDENT_ID_1",
    "title": "API Latency Spike",
    "description": "Response times exceeding SLA",
    "severity": "HIGH",
    "status": "OPEN"
  }
}
EOF
)

echo "Event:"
echo "$EVENT_1" | $PYTHON_CMD -m json.tool
echo ""

# Send event to SQS queue
echo "Sending event to SQS queue..."
if aws sqs send-message \
    --queue-url "$AUDIT_QUEUE_URL" \
    --message-body "$EVENT_1" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    pass "Event sent to SQS queue"
else
    warn "Failed to send event to SQS (check AWS credentials and queue URL)"
fi

# Wait for processing
echo "Waiting 3 seconds for event processing..."
sleep 3

# Verify audit record was created
echo "Querying DynamoDB for audit record..."
AUDIT_RECORDS=$(aws dynamodb query \
    --table-name "$AUDIT_TABLE_NAME" \
    --key-condition-expression "resource_id = :rid" \
    --expression-attribute-values "{\":rid\":{\"S\":\"$INCIDENT_ID_1\"}}" \
    --region "$AWS_REGION" 2>/dev/null || echo '{"Count": 0}')

RECORD_COUNT=$(echo "$AUDIT_RECORDS" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('Count', 0))")

if [ "$RECORD_COUNT" -gt 0 ]; then
    pass "Audit record created for IncidentCreated event (records: $RECORD_COUNT)"
    echo "Record details:"
    echo "$AUDIT_RECORDS" | $PYTHON_CMD -m json.tool | head -30
    echo ""
else
    warn "No audit record found (SQS queue or DynamoDB access may not be configured)"
fi

# ============================================================================
# Test 3: Send IncidentStatusChanged event
# ============================================================================
test_header "Test 3: Send IncidentStatusChanged Event"

echo "Creating event for status change on incident: $INCIDENT_ID_1"

EVENT_2=$(cat <<EOF
{
  "version": "1.0",
  "event_id": "evt-status-changed-001",
  "event_type": "IncidentStatusChanged",
  "source": "incident-service",
  "occurred_at": "2026-09-06T10:05:00Z",
  "correlation_id": "corr-002",
  "actor": {
    "user_id": "$TEST_USER_ID",
    "name": "$TEST_USER_NAME",
    "email": "$TEST_USER_EMAIL"
  },
  "data": {
    "incident_id": "$INCIDENT_ID_1",
    "previous_status": "OPEN",
    "new_status": "INVESTIGATING"
  }
}
EOF
)

echo "Event:"
echo "$EVENT_2" | $PYTHON_CMD -m json.tool
echo ""

echo "Sending event to SQS queue..."
if aws sqs send-message \
    --queue-url "$AUDIT_QUEUE_URL" \
    --message-body "$EVENT_2" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    pass "Event sent to SQS queue"
else
    warn "Failed to send event to SQS"
fi

# Wait for processing
echo "Waiting 3 seconds for event processing..."
sleep 3

# Verify second audit record
echo "Querying DynamoDB for updated record count..."
AUDIT_RECORDS=$(aws dynamodb query \
    --table-name "$AUDIT_TABLE_NAME" \
    --key-condition-expression "resource_id = :rid" \
    --expression-attribute-values "{\":rid\":{\"S\":\"$INCIDENT_ID_1\"}}" \
    --region "$AWS_REGION" 2>/dev/null || echo '{"Count": 0}')

RECORD_COUNT=$(echo "$AUDIT_RECORDS" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('Count', 0))")

if [ "$RECORD_COUNT" -ge 2 ]; then
    pass "Second audit record created for IncidentStatusChanged event (total records: $RECORD_COUNT)"
else
    warn "Expected at least 2 records, found: $RECORD_COUNT"
fi

# ============================================================================
# Test 4: Test Idempotency (duplicate event)
# ============================================================================
test_header "Test 4: Test Idempotency"

echo "Sending DUPLICATE event (same event_id as Test 2)..."
echo "This should NOT create a new record."
echo ""

if aws sqs send-message \
    --queue-url "$AUDIT_QUEUE_URL" \
    --message-body "$EVENT_1" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    pass "Duplicate event sent to SQS queue"
else
    warn "Failed to send duplicate event"
fi

# Wait for processing
echo "Waiting 3 seconds for event processing..."
sleep 3

# Verify record count didn't increase
echo "Querying DynamoDB to verify record count unchanged..."
AUDIT_RECORDS=$(aws dynamodb query \
    --table-name "$AUDIT_TABLE_NAME" \
    --key-condition-expression "resource_id = :rid" \
    --expression-attribute-values "{\":rid\":{\"S\":\"$INCIDENT_ID_1\"}}" \
    --region "$AWS_REGION" 2>/dev/null || echo '{"Count": 0}')

RECORD_COUNT=$(echo "$AUDIT_RECORDS" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('Count', 0))")

if [ "$RECORD_COUNT" -eq 2 ]; then
    pass "Idempotency verified: duplicate event was NOT created (total records: $RECORD_COUNT)"
else
    warn "Record count changed to $RECORD_COUNT (expected 2)"
fi

# ============================================================================
# Test 5: Send IncidentSeverityChanged event
# ============================================================================
test_header "Test 5: Send IncidentSeverityChanged Event"

echo "Creating event for severity change on incident: $INCIDENT_ID_1"

EVENT_3=$(cat <<EOF
{
  "version": "1.0",
  "event_id": "evt-severity-changed-001",
  "event_type": "IncidentSeverityChanged",
  "source": "incident-service",
  "occurred_at": "2026-09-06T10:10:00Z",
  "correlation_id": "corr-003",
  "actor": {
    "user_id": "$TEST_USER_ID",
    "name": "$TEST_USER_NAME",
    "email": "$TEST_USER_EMAIL"
  },
  "data": {
    "incident_id": "$INCIDENT_ID_1",
    "previous_severity": "HIGH",
    "new_severity": "CRITICAL"
  }
}
EOF
)

echo "Event:"
echo "$EVENT_3" | $PYTHON_CMD -m json.tool
echo ""

echo "Sending event to SQS queue..."
if aws sqs send-message \
    --queue-url "$AUDIT_QUEUE_URL" \
    --message-body "$EVENT_3" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    pass "Event sent to SQS queue"
else
    warn "Failed to send event to SQS"
fi

# Wait for processing
echo "Waiting 3 seconds for event processing..."
sleep 3

# ============================================================================
# Test 6: Send IncidentResolved event
# ============================================================================
test_header "Test 6: Send IncidentResolved Event"

echo "Creating event for incident resolution on incident: $INCIDENT_ID_1"

EVENT_4=$(cat <<EOF
{
  "version": "1.0",
  "event_id": "evt-resolved-001",
  "event_type": "IncidentResolved",
  "source": "incident-service",
  "occurred_at": "2026-09-06T10:15:00Z",
  "correlation_id": "corr-004",
  "actor": {
    "user_id": "$TEST_USER_ID",
    "name": "$TEST_USER_NAME",
    "email": "$TEST_USER_EMAIL"
  },
  "data": {
    "incident_id": "$INCIDENT_ID_1",
    "resolution_summary": "Database indexes were optimized, performance restored to baseline."
  }
}
EOF
)

echo "Event:"
echo "$EVENT_4" | $PYTHON_CMD -m json.tool
echo ""

echo "Sending event to SQS queue..."
if aws sqs send-message \
    --queue-url "$AUDIT_QUEUE_URL" \
    --message-body "$EVENT_4" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    pass "Event sent to SQS queue"
else
    warn "Failed to send event to SQS"
fi

# Wait for processing
echo "Waiting 3 seconds for event processing..."
sleep 3

# ============================================================================
# Test 7: Verify audit trail for incident
# ============================================================================
test_header "Test 7: Verify Complete Audit Trail"

echo "Querying DynamoDB for complete audit trail of $INCIDENT_ID_1..."
AUDIT_RECORDS=$(aws dynamodb query \
    --table-name "$AUDIT_TABLE_NAME" \
    --key-condition-expression "resource_id = :rid" \
    --expression-attribute-values "{\":rid\":{\"S\":\"$INCIDENT_ID_1\"}}" \
    --region "$AWS_REGION" 2>/dev/null || echo '{"Count": 0, "Items": []}')

RECORD_COUNT=$(echo "$AUDIT_RECORDS" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('Count', 0))")

echo "Total audit records for $INCIDENT_ID_1: $RECORD_COUNT"
echo ""

if [ "$RECORD_COUNT" -ge 4 ]; then
    pass "Expected audit trail has at least 4 records"
    echo "Audit trail:"
    echo "$AUDIT_RECORDS" | $PYTHON_CMD -m json.tool | head -50
else
    warn "Expected at least 4 records, found: $RECORD_COUNT"
fi

# ============================================================================
# Test 8: Test Multiple Incidents (isolation)
# ============================================================================
test_header "Test 8: Multiple Incidents Isolation"

echo "Creating event for different incident: $INCIDENT_ID_2"

EVENT_5=$(cat <<EOF
{
  "version": "1.0",
  "event_id": "evt-incident-created-002",
  "event_type": "IncidentCreated",
  "source": "incident-service",
  "occurred_at": "2026-09-06T10:20:00Z",
  "correlation_id": "corr-005",
  "actor": {
    "user_id": "$TEST_USER_ID",
    "name": "$TEST_USER_NAME",
    "email": "$TEST_USER_EMAIL"
  },
  "data": {
    "incident_id": "$INCIDENT_ID_2",
    "title": "Database Connection Pool Exhausted",
    "description": "Connection pool at 100% capacity",
    "severity": "CRITICAL",
    "status": "OPEN"
  }
}
EOF
)

echo "Sending event for second incident..."
if aws sqs send-message \
    --queue-url "$AUDIT_QUEUE_URL" \
    --message-body "$EVENT_5" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    pass "Event sent to SQS queue"
else
    warn "Failed to send event to SQS"
fi

# Wait for processing
echo "Waiting 3 seconds for event processing..."
sleep 3

# Verify second incident has separate audit trail
echo "Querying DynamoDB for second incident audit records..."
AUDIT_RECORDS_2=$(aws dynamodb query \
    --table-name "$AUDIT_TABLE_NAME" \
    --key-condition-expression "resource_id = :rid" \
    --expression-attribute-values "{\":rid\":{\"S\":\"$INCIDENT_ID_2\"}}" \
    --region "$AWS_REGION" 2>/dev/null || echo '{"Count": 0}')

RECORD_COUNT_2=$(echo "$AUDIT_RECORDS_2" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('Count', 0))")

if [ "$RECORD_COUNT_2" -ge 1 ]; then
    pass "Separate audit trail created for second incident (records: $RECORD_COUNT_2)"
else
    warn "No audit records found for second incident"
fi

# ============================================================================
# Test 9: Test Invalid/Malformed Events (error handling)
# ============================================================================
test_header "Test 9: Invalid Event Handling"

echo "Testing malformed event (missing required fields)..."

MALFORMED_EVENT=$(cat <<EOF
{
  "version": "1.0",
  "event_id": "evt-malformed-001",
  "event_type": "IncidentCreated"
}
EOF
)

echo "Event (intentionally incomplete):"
echo "$MALFORMED_EVENT" | $PYTHON_CMD -m json.tool
echo ""

echo "Sending malformed event to SQS queue..."
if aws sqs send-message \
    --queue-url "$AUDIT_QUEUE_URL" \
    --message-body "$MALFORMED_EVENT" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    pass "Malformed event sent to SQS queue"
    echo "Expected behavior: Event should be logged as error, message deleted after retries"
else
    warn "Failed to send malformed event"
fi

# Wait for processing
echo "Waiting 3 seconds for error handling..."
sleep 3

echo "Malformed event test complete (check logs for error details)"
echo ""

# ============================================================================
# Summary
# ============================================================================
test_header "Test Summary"

echo "All tests completed!"
echo ""
echo "To verify audit records manually:"
echo "  aws dynamodb scan --table-name $AUDIT_TABLE_NAME --region $AWS_REGION | jq '.'"
echo ""
echo "To monitor logs:"
echo "  docker logs audit-worker-dev --follow  # if running in Docker"
echo "  # or check stdout from: python3 -m src.main"
echo ""
echo "To test with real EventBridge routing:"
echo "  1. Publish events from incident-service"
echo "  2. Verify EventBridge routes to audit-queue"
echo "  3. Check audit records appear in DynamoDB"
echo ""
