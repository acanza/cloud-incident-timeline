#!/bin/bash
# Audit Worker Entrypoint
# Validates configuration and starts SQS consumer
# Handles graceful shutdown on SIGTERM/SIGINT

set -e

SERVICE_NAME="${SERVICE_NAME:-audit-worker}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "=========================================="
echo "Audit Worker Starting Up"
echo "=========================================="
echo "Service: $SERVICE_NAME"
echo "Log Level: $LOG_LEVEL"
echo ""

# Function to validate configuration
validate_config() {
    echo "Validating configuration..."
    
    # Check required environment variables
    required_vars=(
        "AWS_REGION"
        "AUDIT_TABLE_NAME"
        "AUDIT_QUEUE_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "ERROR: Required environment variable not set: $var"
            exit 1
        fi
    done
    
    echo "✓ All required environment variables set"
    echo "  AWS_REGION: $AWS_REGION"
    echo "  AUDIT_TABLE_NAME: $AUDIT_TABLE_NAME"
    echo "  AUDIT_QUEUE_URL: ${AUDIT_QUEUE_URL##*/}"  # Show only queue name
    echo ""
}

# Function to handle signals (graceful shutdown)
handle_signal() {
    echo ""
    echo "Received shutdown signal, gracefully stopping service..."
    
    # Kill SQS Consumer
    if [ -n "$CONSUMER_PID" ] && kill -0 "$CONSUMER_PID" 2>/dev/null; then
        echo "Stopping SQS Consumer (PID $CONSUMER_PID)..."
        kill -TERM "$CONSUMER_PID" 2>/dev/null || true
        wait "$CONSUMER_PID" 2>/dev/null || true
        echo "SQS Consumer stopped"
    fi
    
    echo "=========================================="
    echo "Audit Worker Shutdown Complete"
    echo "=========================================="
    exit 0
}

# Register signal handlers
trap handle_signal SIGTERM SIGINT

# Validate configuration
validate_config

# Start SQS Consumer in background
echo "Starting SQS Consumer..."
python -m src.main &
CONSUMER_PID=$!
echo "✓ SQS Consumer started (PID $CONSUMER_PID)"
echo ""

echo "=========================================="
echo "Audit Worker Ready"
echo "=========================================="
echo ""

# Wait for background process to complete
wait $CONSUMER_PID
CONSUMER_EXIT_CODE=$?

if [ $CONSUMER_EXIT_CODE -ne 0 ]; then
    echo "SQS Consumer exited with code $CONSUMER_EXIT_CODE"
    exit $CONSUMER_EXIT_CODE
fi
