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

# 1. Health check
echo "1. Health check..."
curl -s "$BASE_URL/health" | python -m json.tool
echo ""
echo ""

# 2. Create incident
echo "2. Creating incident..."
RESPONSE=$(curl -s -X POST "$BASE_URL/incidents" \
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

echo "$RESPONSE" | python -m json.tool
INCIDENT_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['incident_id'])")
echo "Created incident: $INCIDENT_ID"
echo ""
echo ""

# 3. List incidents
echo "3. Listing all incidents..."
curl -s "$BASE_URL/incidents" | python -m json.tool
echo ""
echo ""

# 4. Get incident by ID
echo "4. Getting incident by ID ($INCIDENT_ID)..."
curl -s "$BASE_URL/incidents/$INCIDENT_ID" | python -m json.tool
echo ""
echo ""

# 5. Update status to INVESTIGATING
echo "5. Updating status to INVESTIGATING..."
curl -s -X PATCH "$BASE_URL/incidents/$INCIDENT_ID/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "INVESTIGATING",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | python -m json.tool
echo ""
echo ""

# 6. Update severity to CRITICAL
echo "6. Updating severity to CRITICAL..."
curl -s -X PATCH "$BASE_URL/incidents/$INCIDENT_ID/severity" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "CRITICAL",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | python -m json.tool
echo ""
echo ""

# 7. Resolve incident
echo "7. Resolving incident..."
curl -s -X PATCH "$BASE_URL/incidents/$INCIDENT_ID/status" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "RESOLVED",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | python -m json.tool
echo ""
echo ""

# 8. Test validation error
echo "8. Testing validation error (invalid severity)..."
curl -s -X POST "$BASE_URL/incidents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "description": "Test",
    "severity": "INVALID_SEVERITY",
    "actor": {
      "user_id": "test-user-001",
      "email": "test@example.com"
    }
  }' | python -m json.tool
echo ""
echo ""

# 9. Test 404 error
echo "9. Testing 404 error (incident not found)..."
curl -s "$BASE_URL/incidents/inc-nonexistent" | python -m json.tool
echo ""
echo ""

echo "================================================"
echo "Test Complete!"
echo "================================================"
echo "Check http://localhost:8001/docs for interactive API documentation"
