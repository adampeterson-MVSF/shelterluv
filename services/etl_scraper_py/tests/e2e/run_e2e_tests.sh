#!/bin/bash

# E2E Test Runner Script
# Runs live database tests with proper environment setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETL_DIR="$SCRIPT_DIR/../.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🚀 ShelterLuv ETL E2E Tests${NC}"
echo "=================================="

# Safety checks
echo -e "\n${YELLOW}🔍 Safety Checks${NC}"

# Check E2E_LIVE_DB flag
if [[ "${E2E_LIVE_DB}" != "1" ]]; then
    echo -e "${RED}❌ ERROR: E2E_LIVE_DB=1 not set${NC}"
    echo "E2E tests are gated and will be skipped unless E2E_LIVE_DB=1"
    echo "Run with: E2E_LIVE_DB=1 $0"
    exit 1
fi

# Check GCP project
if [[ -z "${GCP_PROJECT}" ]]; then
    echo -e "${RED}❌ ERROR: GCP_PROJECT not set${NC}"
    echo "Set GCP_PROJECT to a non-production project"
    exit 1
fi

# Safety check for production projects
if [[ "${GCP_PROJECT}" =~ (prod|production|live) ]]; then
    echo -e "${RED}❌ ERROR: GCP_PROJECT contains production indicator: ${GCP_PROJECT}${NC}"
    echo "E2E tests should not run against production projects."
    exit 1
fi

echo -e "${GREEN}✅ GCP_PROJECT: ${GCP_PROJECT}${NC}"

# Set default collection if not specified
if [[ -z "${DOGS_COLLECTION}" ]]; then
    export DOGS_COLLECTION="dogs_e2e"
    echo -e "${YELLOW}ℹ️  Using default collection: ${DOGS_COLLECTION}${NC}"
else
    echo -e "${GREEN}✅ DOGS_COLLECTION: ${DOGS_COLLECTION}${NC}"
fi

echo -e "\n${YELLOW}🧪 Running E2E Tests${NC}"
echo "======================"

# Change to ETL directory
cd "$ETL_DIR"

# Run the tests
echo "Running: pytest tests/e2e/ -v --tb=short"
pytest tests/e2e/ -v --tb=short

echo -e "\n${GREEN}✅ E2E Tests Completed${NC}"
