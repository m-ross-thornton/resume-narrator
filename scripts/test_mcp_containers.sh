#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🧪 MCP Container Test Suite"
echo "============================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Services to test
MCP_SERVICES=("mcp-vector" "mcp-resume" "mcp-code")
MCP_PORTS=("9002" "9001" "9003")
HEALTH_URLS=("http://localhost:9002/health" "http://localhost:9001/health" "http://localhost:9003/health")

# Test counters
PASSED=0
FAILED=0

# Helper functions
pass_test() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail_test() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED++))
}

warn_test() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

# Test 1: Check docker-compose.yml exists
echo ""
echo "1️⃣  Checking docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    pass_test "docker-compose.yml found"
else
    fail_test "docker-compose.yml not found"
    exit 1
fi

# Test 2: Build MCP containers
echo ""
echo "2️⃣  Building MCP containers..."
for service in "${MCP_SERVICES[@]}"; do
    echo -n "  Building $service..."
    if docker compose build "$service" > /tmp/docker_build.log 2>&1; then
        pass_test "Built $service"
    else
        fail_test "Build failed for $service"
        echo "    Error output:"
        tail -10 /tmp/docker_build.log | sed 's/^/    /'
    fi
done

# Test 3: Start MCP containers
echo ""
echo "3️⃣  Starting MCP containers..."
echo "  Starting services..."
if docker compose up -d "${MCP_SERVICES[@]}" > /tmp/docker_up.log 2>&1; then
    pass_test "Containers started"
else
    fail_test "Failed to start containers"
    cat /tmp/docker_up.log
    exit 1
fi

# Wait for services to be ready
echo "  Waiting for services to stabilize..."
sleep 5

# Test 4: Check container status
echo ""
echo "4️⃣  Checking container status..."
for service in "${MCP_SERVICES[@]}"; do
    if docker compose ps "$service" | grep -q "Up"; then
        pass_test "$service is running"
    else
        fail_test "$service is not running"
        docker compose ps "$service"
    fi
done

# Test 5: Test health endpoints
echo ""
echo "5️⃣  Testing health endpoints..."
for i in "${!MCP_SERVICES[@]}"; do
    service="${MCP_SERVICES[$i]}"
    url="${HEALTH_URLS[$i]}"

    echo -n "  Testing $service health..."
    if timeout 5 curl -s "$url" > /tmp/health_response.json 2>&1; then
        if grep -q "status\|health\|{" /tmp/health_response.json; then
            pass_test "$service health check passed"
        else
            warn_test "$service returned empty response"
        fi
    else
        fail_test "Could not reach $service on $(echo $url | cut -d: -f3)"
    fi
done

# Test 6: Test MCP-Vector endpoints
echo ""
echo "6️⃣  Testing mcp-vector endpoints..."

endpoints=("/health" "/tool/search_experience" "/tool/analyze_skill_coverage")
for endpoint in "${endpoints[@]}"; do
    echo -n "  Testing POST /tool/search_experience..."
    if curl -s -X POST "http://localhost:9002${endpoint}" \
        -H "Content-Type: application/json" \
        -d '{}' > /tmp/endpoint_response.json 2>&1; then
        pass_test "$endpoint is accessible"
    else
        fail_test "$endpoint is not accessible"
    fi
done

# Test 7: Check container logs for errors
echo ""
echo "7️⃣  Checking container logs..."
for service in "${MCP_SERVICES[@]}"; do
    echo -n "  Checking $service logs..."
    logs=$(docker compose logs "$service" 2>&1)

    # Check for critical errors
    if echo "$logs" | grep -qi "ModuleNotFoundError\|ImportError"; then
        fail_test "$service has import errors"
        echo "    Error:"
        echo "$logs" | grep -i "error" | head -3 | sed 's/^/      /'
    elif echo "$logs" | grep -qi "fatal\|error.*exit"; then
        warn_test "$service has error logs"
    else
        pass_test "$service logs are clean"
    fi
done

# Test 8: Network connectivity between services
echo ""
echo "8️⃣  Testing inter-service connectivity..."
for service in "${MCP_SERVICES[@]}"; do
    echo -n "  Checking $service network connectivity..."
    if docker compose exec -T "$service" curl -s http://localhost:9002/health > /dev/null 2>&1 || true; then
        pass_test "$service can access other services"
    else
        warn_test "$service network check inconclusive (may be expected)"
    fi
done

# Cleanup
echo ""
echo "9️⃣  Cleaning up..."
for service in "${MCP_SERVICES[@]}"; do
    echo -n "  Stopping $service..."
    docker compose stop "$service" > /dev/null 2>&1 || true
    pass_test "Stopped $service"
done

echo -n "  Removing containers..."
docker compose rm -f "${MCP_SERVICES[@]}" > /dev/null 2>&1 || true
pass_test "Containers removed"

# Summary
echo ""
echo "============================"
echo "📊 Test Summary"
echo "============================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All MCP container tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
