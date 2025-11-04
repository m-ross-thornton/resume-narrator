#!/bin/bash

# Resnar Test Runner Script
# Usage: ./run_tests.sh [unit|integration|docker|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test type
TEST_TYPE=${1:-all}

echo -e "${YELLOW}Resnar Test Suite${NC}"
echo "=================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install -r test-requirements.txt"
    exit 1
fi

# Run tests based on type
case $TEST_TYPE in
    unit)
        echo -e "${YELLOW}Running Unit Tests...${NC}"
        pytest tests/ -m unit -v
        ;;
    integration)
        echo -e "${YELLOW}Running Integration Tests...${NC}"
        echo -e "${YELLOW}Make sure services are running: docker-compose up -d${NC}"
        pytest tests/ -m integration -v
        ;;
    docker)
        echo -e "${YELLOW}Running Docker Configuration Tests...${NC}"
        pytest tests/test_docker_deployment.py -v
        ;;
    all)
        echo -e "${YELLOW}Running All Tests...${NC}"
        pytest tests/ -v
        ;;
    *)
        echo "Usage: $0 [unit|integration|docker|all]"
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Tests passed!${NC}"
else
    echo -e "${RED}✗ Tests failed!${NC}"
    exit 1
fi
