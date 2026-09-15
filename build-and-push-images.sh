#!/bin/bash

# ============================================================================
# Build and push Docker images to ECR with correct architecture (amd64)
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get AWS Account ID dynamically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Error: Could not retrieve AWS Account ID. Check AWS credentials.${NC}"
    exit 1
fi

# Configuration
AWS_REGION="eu-west-3"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
SERVICES=("incident-service" "timeline-service" "audit-worker")

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Building & Pushing Docker Images${NC}"
echo -e "${YELLOW}================================${NC}"
echo "AWS Region: $AWS_REGION"
echo "ECR Registry: $ECR_REGISTRY"
echo "Services: ${SERVICES[*]}"
echo ""

# Step 1: Login to ECR
echo -e "${YELLOW}[1/4] Logging in to ECR...${NC}"
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_REGISTRY"
echo -e "${GREEN}✓ ECR login successful${NC}"
echo ""

# Step 2: Build and push each service
for SERVICE in "${SERVICES[@]}"; do
  echo -e "${YELLOW}[2/4] Building $SERVICE for architecture: linux/amd64${NC}"
  
  SERVICE_DIR="services/$SERVICE"
  if [ ! -d "$SERVICE_DIR" ]; then
    echo -e "${RED}✗ Directory not found: $SERVICE_DIR${NC}"
    exit 1
  fi
  
  # Build with correct platform (linux/amd64 for AWS Fargate)
  docker build \
    --platform linux/amd64 \
    -t "${ECR_REGISTRY}/cloud-incident-timeline-dev-${SERVICE}:latest" \
    "$SERVICE_DIR"
  
  echo -e "${GREEN}✓ $SERVICE built successfully${NC}"
  echo ""
  
  echo -e "${YELLOW}[3/4] Pushing $SERVICE to ECR...${NC}"
  docker push "${ECR_REGISTRY}/cloud-incident-timeline-dev-${SERVICE}:latest"
  echo -e "${GREEN}✓ $SERVICE pushed successfully${NC}"
  echo ""
done

echo -e "${YELLOW}[4/4] Verifying images in ECR...${NC}"
for SERVICE in "${SERVICES[@]}"; do
  REPO_NAME="cloud-incident-timeline-dev-${SERVICE}"
  IMAGES=$(aws ecr describe-images \
    --repository-name "$REPO_NAME" \
    --region "$AWS_REGION" \
    --query 'imageDetails[*].[imageTags,imageDigest]' \
    --output text)
  
  echo "Repository: $REPO_NAME"
  echo "$IMAGES" | while read -r tags digest; do
    echo "  Tags: $tags | Digest: ${digest:0:20}..."
  done
done

echo ""
echo -e "${GREEN}✓ All images built and pushed successfully!${NC}"
