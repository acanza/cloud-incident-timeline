#!/bin/bash
# Quick test script for incident-service endpoints
# Run this after starting the service with: python -m uvicorn src.main:app --reload

set -e

BASE_URL="http://localhost:8001"
INCIDENT_ID=""

echo "================================================"
echo "Testing Incident Service API"
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
    echo "  cd services/incident-service"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo "  python3 -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8001"
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

# 2. Create incident
echo "2. Creating incident..."
RESPONSE=$(curl -s --max-time 10 -X POST "$BASE_URL/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database CPU spike",
    "description": "Production database showing high CPU usage",
    "severity": "HIGH",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }')

echo "$RESPONSE" | $PYTHON_CMD -m json.tool
INCIDENT_ID=$(echo "$RESPONSE" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin)['incident_id'])")
echo "Created incident: $INCIDENT_ID"
echo ""
echo ""

# 3. List incidents
echo "3. Listing all incidents..."
curl -s --max-time 10 "$BASE_URL/incidents" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 4. Get incident by ID
echo "4. Getting incident by ID ($INCIDENT_ID)..."
curl -s --max-time 10 "$BASE_URL/incidents/$INCIDENT_ID" | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 5. Update status to INVESTIGATING
echo "5. Updating status to INVESTIGATING..."
curl -s --max-time 10 -X PATCH "$BASE_URL/incidents/$INCIDENT_ID/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "INVESTIGATING",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 6. Update severity to CRITICAL
echo "6. Updating severity to CRITICAL..."
curl -s --max-time 10 -X PATCH "$BASE_URL/incidents/$INCIDENT_ID/severity" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "CRITICAL",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 7. Resolve incident
echo "7. Resolving incident..."
curl -s --max-time 10 -X PATCH "$BASE_URL/incidents/$INCIDENT_ID/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "RESOLVED",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 8. Test validation error
echo "8. Testing validation error (invalid severity)..."
curl -s --max-time 10 -X POST "$BASE_URL/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "description": "Test",
    "severity": "INVALID_SEVERITY",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | $PYTHON_CMD -m json.tool
echo ""
echo ""

# 9. Test 404 error
echo "9. Testing 404 error (incident not found)..."
curl -s --max-time 10 "$BASE_URL/incidents/inc-nonexistent" | $PYTHON_CMD -m json.tool
echo ""
echo ""

echo "================================================"
echo "Test Complete!"
echo "================================================"
echo "Check http://localhost:8001/docs for interactive API documentation"
