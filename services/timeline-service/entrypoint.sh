#!/bin/bash
# Timeline Service Entrypoint
# Orchestrates FastAPI HTTP server and SQS consumer concurrently
# Handles graceful shutdown on SIGTERM/SIGINT

set -e

SERVICE_NAME="${SERVICE_NAME:-timeline-service}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
PORT="${PORT:-8080}"

echo "=========================================="
echo "Timeline Service Starting Up"
echo "=========================================="
echo "Service: $SERVICE_NAME"
echo "Port: $PORT"
echo "Log Level: $LOG_LEVEL"
echo ""

# Function to handle signals (graceful shutdown)
handle_signal() {
    echo ""
    echo "Received shutdown signal, gracefully stopping services..."
    
    # Kill FastAPI
    if [ -n "$FASTAPI_PID" ] && kill -0 "$FASTAPI_PID" 2>/dev/null; then
        echo "Stopping FastAPI (PID $FASTAPI_PID)..."
        kill -TERM "$FASTAPI_PID" 2>/dev/null || true
        wait "$FASTAPI_PID" 2>/dev/null || true
        echo "FastAPI stopped"
    fi
    
    # Kill SQS Consumer
    if [ -n "$CONSUMER_PID" ] && kill -0 "$CONSUMER_PID" 2>/dev/null; then
        echo "Stopping SQS Consumer (PID $CONSUMER_PID)..."
        kill -TERM "$CONSUMER_PID" 2>/dev/null || true
        wait "$CONSUMER_PID" 2>/dev/null || true
        echo "SQS Consumer stopped"
    fi
    
    echo "=========================================="
    echo "Timeline Service Shutdown Complete"
    echo "=========================================="
    exit 0
}

# Register signal handlers
trap handle_signal SIGTERM SIGINT

# Start FastAPI HTTP Server
echo "Starting FastAPI HTTP server on port $PORT..."
python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level "${LOG_LEVEL,,}" \
    &
FASTAPI_PID=$!
echo "FastAPI started (PID $FASTAPI_PID)"
echo ""

# Give FastAPI a moment to start
sleep 2

# Start SQS Consumer
echo "Starting SQS Consumer..."
python3 << 'EOF'
from src.services.sqs_consumer import SQSConsumer
from src.logger import setup_logger
from src.config import Config
import sys

try:
    logger = setup_logger(__name__, Config.LOG_LEVEL)
    logger.info("SQS Consumer starting up")
    consumer = SQSConsumer()
    consumer.start()
except Exception as e:
    logger.error(f"SQS Consumer failed to start: {str(e)}")
    sys.exit(1)
EOF
CONSUMER_PID=$!
echo "SQS Consumer started (PID $CONSUMER_PID)"
echo ""

echo "=========================================="
echo "Timeline Service Ready"
echo "=========================================="
echo "HTTP API: http://localhost:$PORT"
echo "Health Check: http://localhost:$PORT/health"
echo "Swagger: http://localhost:$PORT/docs"
echo "ReDoc: http://localhost:$PORT/redoc"
echo ""
echo "Processes running:"
echo "  - FastAPI (PID $FASTAPI_PID)"
echo "  - SQS Consumer (PID $CONSUMER_PID)"
echo ""
echo "Press Ctrl+C to shutdown"
echo "=========================================="
echo ""

# Wait for both processes
# If either dies, the script will also exit
wait $FASTAPI_PID $CONSUMER_PID
