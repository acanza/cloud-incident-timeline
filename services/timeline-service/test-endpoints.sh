#!/bin/bash
# Quick test script for timeline-service endpoints
# Run this after starting the service with: python -m uvicorn src.main:app --reload --port 8002

set -e

BASE_URL="http://localhost:8002"
INCIDENT_ID="inc-test-001"

echo "================================================"
echo "Testing Timeline Service API"
echo "================================================"
echo ""

# Detect Python interpreter: prefer 'python', fall back to 'python3'
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Error: Neither 'python' nor 'python3' found. Please install Python and ensure it's in your PATH."
    exit 1
fi

echo "Using Python interpreter: $PYTHON_CMD"
echo ""

# Pre-flight check: verify service is running
echo "Checking if service is running at $BASE_URL..."
if ! curl -s --max-time 5 "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ ERROR: Service is not responding at $BASE_URL"
    echo ""
    echo "Make sure the service is running:"
    echo "  cd services/timeline-service"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  # Configure .env with AWS credentials and table names"
    echo "  python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8002"
    echo ""
    exit 1
fi
echo "✅ Service is reachable"
echo ""

# 1. Health check
echo "1. Health check..."
curl -s --max-time 10 "$BASE_URL/health" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 2. Get timeline (empty at first)
echo "2. Getting timeline for incident (initially empty)..."
curl -s --max-time 10 "$BASE_URL/incidents/$INCIDENT_ID/timeline" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 3. Add comment 1
echo "3. Adding first comment..."
RESPONSE_1=$(curl -s --max-time 10 -X POST "$BASE_URL/incidents/$INCIDENT_ID/timeline/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Backend team is investigating database metrics",
    "user_id": "user-001"
  }')

echo "$RESPONSE_1" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 4. Add comment 2
echo "4. Adding second comment..."
RESPONSE_2=$(curl -s --max-time 10 -X POST "$BASE_URL/incidents/$INCIDENT_ID/timeline/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Database optimization complete, monitoring for stability",
    "user_id": "user-002"
  }')

echo "$RESPONSE_2" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 5. Get timeline (with comments)
echo "5. Getting timeline with comments..."
curl -s --max-time 10 "$BASE_URL/incidents/$INCIDENT_ID/timeline" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 6. Add comment with long text
echo "6. Adding comment with longer text..."
curl -s --max-time 10 -X POST "$BASE_URL/incidents/$INCIDENT_ID/timeline/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "Extended investigation: Found N+1 queries in incident retrieval endpoint. Implemented caching layer and optimized database indexes. Performance improved by 40%. All systems nominal.",
    "user_id": "user-003"
  }' | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 7. Test validation error (missing comment)
echo "7. Testing validation error (missing comment)..."
curl -s --max-time 10 -X POST "$BASE_URL/incidents/$INCIDENT_ID/timeline/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-001"
  }' | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 8. Test validation error (empty comment)
echo "8. Testing validation error (empty comment)..."
curl -s --max-time 10 -X POST "$BASE_URL/incidents/$INCIDENT_ID/timeline/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "comment": "",
    "user_id": "user-001"
  }' | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 9. Test validation error (comment too long - over 1000 chars)
echo "9. Testing validation error (comment too long)..."
LONG_COMMENT=$(printf 'A%.0s' {1..1001})
curl -s --max-time 10 -X POST "$BASE_URL/incidents/$INCIDENT_ID/timeline/comments" \
  -H "Content-Type: application/json" \
  -d "{
    \"comment\": \"$LONG_COMMENT\",
    \"user_id\": \"user-001\"
  }" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 10. Test validation error (invalid incident_id format)
echo "10. Testing validation error (invalid incident_id)..."
curl -s --max-time 10 "$BASE_URL/incidents//timeline" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 11. Get timeline for different incident
echo "11. Getting timeline for another incident (should be empty)..."
curl -s --max-time 10 "$BASE_URL/incidents/inc-test-002/timeline" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 12. Final timeline for original incident
echo "12. Final timeline for original incident ($INCIDENT_ID)..."
curl -s --max-time 10 "$BASE_URL/incidents/$INCIDENT_ID/timeline" | $PYTHON_CMD -m json.tool
echo ""
echo ""

echo "================================================"
echo "Test Complete!"
echo "================================================"
echo ""
echo "✅ Timeline service endpoints tested successfully!"
echo ""
echo "Interactive API documentation available at:"
echo "  Swagger UI: http://localhost:8002/docs"
echo "  ReDoc:      http://localhost:8002/redoc"
echo ""
echo "Timeline service features:"
echo "  - GET /health - Health check for ALB"
echo "  - GET /incidents/{incident_id}/timeline - Query timeline"
echo "  - POST /incidents/{incident_id}/timeline/comments - Add comment"
echo ""
