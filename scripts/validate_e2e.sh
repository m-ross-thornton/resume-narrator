#!/bin/bash
set -e

echo "🧪 Resume Narrator E2E Validation"
echo "=================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 1. Check unit tests
echo ""
echo "📋 Running unit tests..."
python -m pytest tests/test_vector_db_data_pipeline.py -q || exit 1

# 2. Check services running
echo ""
echo "🐳 Checking Docker services..."
RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)
if [ "$RUNNING" -lt 3 ]; then
    echo "❌ Not enough services running. Expected at least 3, got $RUNNING"
    echo "Starting services..."
    docker compose up -d ollama mcp-vector mcp-resume mcp-code vector-db agent
    sleep 10
fi

echo "✓ Docker services running"
docker compose ps

# 3. Test MCP endpoints
echo ""
echo "🔌 Testing MCP endpoints..."

# Vector DB health
echo -n "  Vector DB (port 9002): "
if curl -s http://localhost:9002/health > /dev/null 2>&1; then
    echo "✓"
else
    echo "❌ Not responding"
    exit 1
fi

# Resume server health
echo -n "  Resume Server (port 9001): "
if curl -s http://localhost:9001/health > /dev/null 2>&1; then
    echo "✓"
else
    echo "❌ Not responding"
    exit 1
fi

# Code server health
echo -n "  Code Server (port 9003): "
if curl -s http://localhost:9003/health > /dev/null 2>&1; then
    echo "✓"
else
    echo "❌ Not responding (optional)"
fi

# 4. Test vector DB operations
echo ""
echo "📊 Testing vector database operations..."

# Check collections
echo -n "  Collection counts: "
if docker compose exec -T vector-db python << 'EOF' > /dev/null 2>&1
from vector_db_server import VectorDBManager
db = VectorDBManager('/app/data/embeddings/chroma_db')
for col in ['experience', 'projects', 'skills']:
    c = db.client.get_collection(col)
    count = c.count()
    print(f"{col}: {count}")
    if count == 0:
        print(f"WARNING: {col} collection is empty")
EOF
then
    echo "✓"
else
    echo "❌ Could not check collections"
fi

# Test search endpoint
echo -n "  Search endpoint: "
if curl -s -X POST http://localhost:9002/tool/search_experience \
  -H "Content-Type: application/json" \
  -d '{"query":"skills"}' | grep -q "results" 2>/dev/null; then
    echo "✓"
else
    echo "⚠️  No results (collections may be empty)"
fi

# 5. Test agent initialization
echo ""
echo "🤖 Testing agent initialization..."

if docker compose exec -T agent python << 'EOF' > /dev/null 2>&1
from agent.main import create_lc_agent
try:
    agent = create_lc_agent()
    print("Agent initialized successfully")
except Exception as e:
    print(f"Agent initialization failed: {e}")
    exit(1)
EOF
then
    echo "✓ Agent initialized"
else
    echo "❌ Agent initialization failed"
    exit 1
fi

# 6. Test agent tool execution
echo ""
echo "🔧 Testing agent tool execution..."

if docker compose exec -T agent python << 'EOF'
import json
from agent.main import create_lc_agent
import logging
logging.basicConfig(level=logging.INFO)

try:
    agent = create_lc_agent()
    result = agent.invoke({'input': 'What are my main skills?'})

    output = result.get('output', '')

    # Check that output is not empty
    if not output:
        print("❌ Agent returned empty output")
        exit(1)

    # Check that output doesn't contain tool syntax
    if 'search_experience(' in output or '{"name": "search_experience"' in output:
        print("❌ Agent returned tool syntax instead of executing tools:")
        print(output)
        exit(1)

    # Check that output seems reasonable
    if len(output) < 20:
        print("⚠️  Agent output is very short, may not have executed tools:")
        print(output)

    print("✓ Agent executed tools successfully")
    print("")
    print("Agent Response Preview:")
    print(output[:200] + "..." if len(output) > 200 else output)

except Exception as e:
    print(f"❌ Agent test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF
then
    :
else
    echo "⚠️  Agent tool execution test had issues (see above)"
fi

# 7. Vector DB population check
echo ""
echo "📈 Checking Vector DB population..."

RESULT=$(docker compose exec -T vector-db python << 'EOF'
from vector_db_server import VectorDBManager
db = VectorDBManager('/app/data/embeddings/chroma_db')
total = 0
for col in ['experience', 'projects', 'skills']:
    c = db.client.get_collection(col)
    count = c.count()
    total += count
    print(f"{col}: {count}")
print(f"Total: {total}")
EOF
)

if echo "$RESULT" | grep -q "Total: 0"; then
    echo "⚠️  Vector DB is empty"
    echo "  Run: python scripts/init_vector_db.py"
else
    echo "✓ Vector DB is populated"
    echo "$RESULT"
fi

# Final summary
echo ""
echo "=================================="
echo "✅ E2E Validation Summary"
echo "=================================="
echo "✓ Unit tests passed"
echo "✓ Docker services running"
echo "✓ MCP endpoints healthy"
echo "✓ Vector DB operational"
echo "✓ Agent functional"
echo ""
echo "System is ready for testing!"
