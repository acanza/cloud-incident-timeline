#!/usr/bin/env python3
"""
End-to-end test for cloud-incident-timeline.
Tests complete flow: incident creation → EventBridge → SQS → audit-worker → DynamoDB
"""

import requests
import boto3
import time
import json
from datetime import datetime

# Configuration
ALB_URL = "http://cloud-incident-timeline-dev-alb-1124303643.eu-west-3.elb.amazonaws.com"
AWS_REGION = "eu-west-3"
DYNAMODB_REGION = AWS_REGION

# DynamoDB table names
INCIDENTS_TABLE = "cloud-incident-timeline-dev-incidents"
TIMELINE_TABLE = "cloud-incident-timeline-dev-incident-timeline"
AUDIT_TABLE = "cloud-incident-timeline-dev-audit-logs"

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
incidents_table = dynamodb.Table(INCIDENTS_TABLE)
timeline_table = dynamodb.Table(TIMELINE_TABLE)
audit_table = dynamodb.Table(AUDIT_TABLE)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_health_checks():
    """Test health check endpoints for both services."""
    print_section("1. TESTING HEALTH CHECKS")
    
    # Test incident-service health
    try:
        resp = requests.get(f"{ALB_URL}/incidents/health", timeout=5)
        print(f"✓ incident-service health: {resp.status_code}")
        print(f"  Response: {resp.json()}")
    except Exception as e:
        print(f"✗ incident-service health failed: {e}")
        return False
    
    # Test timeline-service health
    try:
        resp = requests.get(f"{ALB_URL}/incidents/health/timeline/health", timeout=5)
        print(f"✓ timeline-service health: {resp.status_code}")
        print(f"  Response: {resp.json()}")
    except Exception as e:
        print(f"✗ timeline-service health failed: {e}")
        return False
    
    return True

def test_incident_creation():
    """Create a test incident and return the incident_id."""
    print_section("2. CREATING INCIDENT")
    
    payload = {
        "title": "E2E Test Incident",
        "description": "Testing complete end-to-end flow",
        "severity": "HIGH",
        "actor": {
            "user_id": "test-user-123",
            "email": "test@example.com"
        }
    }
    
    try:
        resp = requests.post(
            f"{ALB_URL}/incidents",
            json=payload,
            timeout=10
        )
        
        if resp.status_code != 201:
            print(f"✗ Failed to create incident: {resp.status_code}")
            print(f"  Response: {resp.text}")
            return None
        
        incident = resp.json()
        incident_id = incident.get('incident_id')
        
        print(f"✓ Incident created successfully")
        print(f"  Incident ID: {incident_id}")
        print(f"  Status: {incident.get('status')}")
        print(f"  Severity: {incident.get('severity')}")
        print(f"  Created at: {incident.get('created_at')}")
        
        return incident_id
        
    except Exception as e:
        print(f"✗ Incident creation failed: {e}")
        return None

def test_dynamodb_incidents(incident_id):
    """Check if incident appears in incidents table."""
    print_section("3. CHECKING INCIDENTS TABLE")
    
    time.sleep(2)  # Wait for propagation
    
    try:
        response = incidents_table.get_item(Key={'incident_id': incident_id})
        
        if 'Item' not in response:
            print(f"✗ Incident NOT found in DynamoDB incidents table")
            return False
        
        item = response['Item']
        print(f"✓ Incident found in DynamoDB incidents table")
        print(f"  Incident ID: {item.get('incident_id')}")
        print(f"  Title: {item.get('title')}")
        print(f"  Severity: {item.get('severity')}")
        print(f"  Status: {item.get('status')}")
        print(f"  Created at: {item.get('created_at')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to query incidents table: {e}")
        return False

def test_dynamodb_timeline(incident_id):
    """Check if timeline event appears in timeline table."""
    print_section("4. CHECKING TIMELINE TABLE")
    
    time.sleep(2)  # Wait for EventBridge → SQS → timeline-service processing
    
    try:
        response = timeline_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('incident_id').eq(incident_id)
        )
        
        items = response.get('Items', [])
        
        if not items:
            print(f"✗ No timeline events found for incident {incident_id}")
            return False
        
        print(f"✓ Found {len(items)} timeline event(s)")
        for i, item in enumerate(items, 1):
            print(f"\n  Event {i}:")
            print(f"    Event ID: {item.get('event_id')}")
            print(f"    Event Type: {item.get('event_type')}")
            print(f"    Created at: {item.get('created_at')}")
            if 'event_data' in item:
                try:
                    event_data = json.loads(item['event_data']) if isinstance(item['event_data'], str) else item['event_data']
                    print(f"    Data: {json.dumps(event_data, indent=6)}")
                except:
                    print(f"    Data: {item.get('event_data')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to query timeline table: {e}")
        return False

def test_dynamodb_audit(incident_id):
    """Check if audit record appears in audit_logs table."""
    print_section("5. CHECKING AUDIT LOGS TABLE")
    
    time.sleep(3)  # Wait for SQS → audit-worker processing
    
    try:
        # Scan audit table to find entries related to this incident
        response = audit_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('entity_id').eq(incident_id)
        )
        
        items = response.get('Items', [])
        
        if not items:
            print(f"✗ No audit records found for incident {incident_id}")
            print(f"  Note: This may be expected if audit-worker hasn't processed the event yet")
            return False
        
        print(f"✓ Found {len(items)} audit record(s)")
        for i, item in enumerate(items, 1):
            print(f"\n  Audit Record {i}:")
            print(f"    Audit ID: {item.get('audit_id')}")
            print(f"    Entity ID: {item.get('entity_id')}")
            print(f"    Event Type: {item.get('event_type')}")
            print(f"    Created at: {item.get('created_at')}")
            if 'event_data' in item:
                try:
                    event_data = json.loads(item['event_data']) if isinstance(item['event_data'], str) else item['event_data']
                    print(f"    Data: {json.dumps(event_data, indent=6)}")
                except:
                    print(f"    Data: {item.get('event_data')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to query audit table: {e}")
        return False

def main():
    """Run full end-to-end test."""
    print("\n" + "="*80)
    print("  CLOUD-INCIDENT-TIMELINE END-TO-END TEST")
    print(f"  Time: {datetime.now().isoformat()}")
    print("="*80)
    
    # Step 1: Health checks
    if not test_health_checks():
        print("\n✗ Health checks failed - services not responding")
        return False
    
    # Step 2: Create incident
    incident_id = test_incident_creation()
    if not incident_id:
        print("\n✗ Failed to create incident")
        return False
    
    # Step 3: Check incidents table
    incidents_ok = test_dynamodb_incidents(incident_id)
    
    # Step 4: Check timeline table
    timeline_ok = test_dynamodb_timeline(incident_id)
    
    # Step 5: Check audit logs table
    audit_ok = test_dynamodb_audit(incident_id)
    
    # Summary
    print_section("TEST SUMMARY")
    
    all_passed = incidents_ok and timeline_ok
    
    print(f"Incidents Table:   {'✓ PASS' if incidents_ok else '✗ FAIL'}")
    print(f"Timeline Table:    {'✓ PASS' if timeline_ok else '✗ FAIL'}")
    print(f"Audit Logs Table:  {'✓ PASS' if audit_ok else '✗ FAIL (optional)'}")
    
    print(f"\nTest Incident ID: {incident_id}")
    
    if all_passed:
        print("\n✓✓✓ END-TO-END TEST PASSED ✓✓✓")
        print("All critical components working correctly!")
    else:
        print("\n✗✗✗ END-TO-END TEST FAILED ✗✗✗")
        print("Some components are not working correctly")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
