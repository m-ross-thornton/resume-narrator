# End-to-End Testing Guide for Resume Narrator

This guide covers comprehensive testing of the Resume Narrator system, from local development through production deployment.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (Chainlit)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                 Agent (LLM + Tool Execution)                │
│        - CustomReActAgent with tool call parsing            │
│        - Makes HTTP calls to MCP servers                     │
└─────────────┬──────────────────┬──────────────┬─────────────┘
              │                  │              │
              ↓                  ↓              ↓
        ┌──────────┐      ┌──────────┐    ┌──────────┐
        │  Vector  │      │ Document │    │Code Info │
        │   DB     │      │ Parser   │    │ Extractor│
        │ (Resume) │      │(MCP)     │    │ (MCP)    │
        └──────────┘      └──────────┘    └──────────┘
```

## Testing Levels

### 1. Unit Tests (Local Development)

Run the vector database data pipeline tests:

```bash
python -m pytest tests/test_vector_db_data_pipeline.py -v
```

Expected output:
- All 15 tests should pass
- Tests cover:
  - Data file existence
  - JSON validity
  - Vector database indexing
  - Semantic search
  - Full pipeline integration

### 2. Integration Tests (Docker Compose)

#### Prerequisite: Start services

```bash
docker compose up -d ollama mcp-vector mcp-resume mcp-code vector-db agent
```

Verify all services are running:

```bash
docker compose ps
```

Expected services:
- ollama (port 11434)
- mcp-vector (port 9002)
- mcp-resume (port 9001)
- mcp-code (port 9003)
- vector-db (port 8000)
- agent (connected to all services)

#### Test 1: Vector DB Service Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "collections": ["experience", "projects", "skills"]}
```

#### Test 2: Search Experience Tool

```bash
curl -X POST http://localhost:9002/tool/search_experience \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning"}'
```

Expected response:
```json
{
  "results": [
    {
      "id": "experience_...",
      "document": "...",
      "metadata": {...},
      "similarity": 0.85
    }
  ]
}
```

#### Test 3: Skill Analysis Tool

```bash
curl -X POST http://localhost:9002/tool/analyze_skill_coverage \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected response:
```json
{
  "total_skills": 30,
  "categories": {...},
  "analysis": "..."
}
```

#### Test 4: Agent Tool Invocation

Test the agent directly:

```bash
docker compose exec agent python -c "
from agent.main import create_lc_agent
agent = create_lc_agent()
result = agent.invoke({'input': 'What are my main skills?'})
print(result['output'])
"
```

Expected:
- Response should contain actual skill information, NOT tool call syntax
- Should reference tools being called (in logs): `Executing tool: search_experience`
- Should contain facts from the vector database

### 3. System Tests (Full Docker Environment)

#### Test Scenario: Verify Complete Data Pipeline

1. **Initialize Vector DB:**
   ```bash
   docker compose run --rm init_vector_db
   ```

2. **Check collections are populated:**
   ```bash
   docker compose exec vector-db python -c "
   from vector_db_server import VectorDBManager
   db = VectorDBManager('/app/data/embeddings/chroma_db')
   collections = ['experience', 'projects', 'skills']
   for col in collections:
       c = db.client.get_collection(col)
       print(f'{col}: {c.count()} documents')
   "
   ```

3. **Verify agent can access tools:**
   ```bash
   docker compose logs agent | grep -E "Executing tool|Successfully"
   ```

4. **Test through Chainlit UI:**
   - Navigate to http://localhost:8000
   - Ask: "What is my professional background?"
   - Expected: Agent responds with work history from vector DB
   - Not expected: Tool call syntax in response

#### Test Scenario: Validate Auto-Updater

1. **Simulate webhook:**
   ```bash
   curl -X POST http://localhost:8008 \
     -H "Content-Type: application/json" \
     -d '{"event": "push", "repository": "resnar"}'
   ```

2. **Monitor logs:**
   ```bash
   docker compose logs autoupdater -f
   ```

3. **Verify deployment:**
   - Check that git pull succeeds
   - Check that containers are updated
   - Verify port 8008 is freed properly
   - Verify no port binding conflicts

## End-to-End Test Scenarios

### Scenario 1: User Asks About Work Experience

**User Input:** "What AI projects have I worked on?"

**Expected Flow:**
1. Chainlit sends message to agent
2. Agent receives message, identifies `search_experience` tool is needed
3. Agent parses tool call from LLM output
4. Agent executes HTTP call to vector DB server
5. Vector DB searches for "AI projects" in experience collection
6. Results returned with similarity scores
7. Agent formulates response based on search results
8. Chainlit displays response to user

**Expected Result:**
- User sees: "Based on your experience, you have worked on [AI projects with details]"
- NOT: `search_experience(query="AI projects")`

### Scenario 2: User Asks for Resume

**User Input:** "Generate my resume"

**Expected Flow:**
1. Agent detects `generate_resume_pdf` tool is needed
2. Agent executes tool with appropriate parameters
3. MCP resume server generates PDF
4. Agent provides link/attachment to user

**Expected Result:**
- Resume PDF is generated
- User can download it

### Scenario 3: Hybrid Vector DB Initialization

**First deployment:**
```bash
# Vector DB is empty
docker compose run --rm init_vector_db
# Output: Initializes all collections, indexes 15 documents total
```

**Subsequent deployments:**
```bash
# Vector DB already has data
docker compose run --rm init_vector_db
# Output: Skips initialization, uses existing data (fast)
```

**Force re-initialization:**
```bash
docker compose run --rm init_vector_db --force
# Output: Clears and rebuilds all collections
```

## Testing Checklist

### Pre-Deployment

- [ ] All unit tests pass: `pytest tests/test_vector_db_data_pipeline.py`
- [ ] All services start without errors: `docker compose up -d`
- [ ] Vector DB contains correct number of documents (15 total)
- [ ] Agent can execute tools and return actual results
- [ ] No tool call syntax appears in agent responses
- [ ] All MCP endpoints respond to health checks
- [ ] Docker daemon access is properly configured

### Deployment (Auto-Updater)

- [ ] Webhook is properly triggered on git push
- [ ] Git pull succeeds without conflicts
- [ ] Old containers are cleaned up properly
- [ ] Port 8008 is freed before rebinding
- [ ] Containers are rebuilt with latest code
- [ ] Services start successfully
- [ ] No port binding conflicts occur
- [ ] Monitoring stack is optional (doesn't block deployment)

### Post-Deployment

- [ ] Agent responds to user queries
- [ ] Vector DB search returns relevant results
- [ ] Tool execution completes without errors
- [ ] Responses contain actual information (not tool syntax)
- [ ] Agent logs show successful tool invocations
- [ ] Vector DB collections are populated

## Common Issues and Troubleshooting

### Agent Returns Tool Syntax Instead of Results

**Symptom:** User sees: `search_experience(query="...")`

**Causes:**
1. Tool execution failed silently
2. Tool parsing regex didn't match LLM output format
3. MCP server is unreachable

**Fix:**
```bash
# Check agent logs
docker compose logs agent | grep -i error

# Check MCP server health
curl http://localhost:9002/health

# Test tool directly
curl -X POST http://localhost:9002/tool/search_experience \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

### Vector DB Initialization Fails

**Symptom:** Collections have 0 documents

**Check:**
1. Data files exist: `ls data/experience/`
2. Ollama is running: `curl http://ollama:11434/api/tags`
3. ChromaDB path is writable: `ls -la data/embeddings/`

**Fix:**
```bash
# Manually run data pipeline
python scripts/populate_experience_data.py
python scripts/load_experience_to_vector_db.py

# Verify
python scripts/init_vector_db.py --check-only
```

### Port Binding Conflicts

**Symptom:** `bind for port 8008 failed, port already allocated`

**Fix:**
```bash
# Force recreation of autoupdater
docker compose up -d --build --force-recreate autoupdater

# Or clean and restart
docker compose rm -f autoupdater
docker compose up -d autoupdater
```

### Docker Daemon Not Accessible

**Symptom:** `Cannot connect to Docker daemon`

**In auto-updater container:**
```bash
# Check socket exists
docker exec project-autoupdater-1 ls -la /var/run/docker.sock

# Check permissions
docker exec project-autoupdater-1 docker ps
```

## Performance Baselines

### Expected Response Times

| Operation | Time | Notes |
|-----------|------|-------|
| Vector DB search | 100-300ms | Semantic similarity search |
| Agent tool execution | 500ms-2s | Network roundtrip + LLM |
| Resume PDF generation | 1-3s | Server-side rendering |
| Full agent response | 2-5s | LLM + tools + formatting |

### Data Pipeline

| Stage | Time | Volume |
|-------|------|--------|
| PDF parsing | 2-3s | 1 resume PDF |
| Work history extraction | 30-60s | Using Ollama |
| Vector embedding | 2-5s | 15 documents |
| Total initialization | 45-75s | Fresh deployment |

## Validation Script

Save as `scripts/validate_e2e.sh`:

```bash
#!/bin/bash
set -e

echo "🧪 Resume Narrator E2E Validation"
echo "=================================="

# 1. Check unit tests
echo "📋 Running unit tests..."
python -m pytest tests/test_vector_db_data_pipeline.py -q || exit 1

# 2. Check services running
echo "🐳 Checking Docker services..."
docker compose ps --services --filter "status=running" | wc -l
docker compose ps | grep "Up" || exit 1

# 3. Test MCP endpoints
echo "🔌 Testing MCP endpoints..."
curl -s http://localhost:9002/health | grep -q "healthy" || exit 1
curl -s http://localhost:9001/health | grep -q "healthy" || exit 1

# 4. Test vector DB
echo "📊 Testing vector database..."
curl -s -X POST http://localhost:9002/tool/search_experience \
  -H "Content-Type: application/json" \
  -d '{"query":"test"}' | grep -q "results" || exit 1

# 5. Test agent
echo "🤖 Testing agent..."
docker compose exec -T agent python -c "
from agent.main import create_lc_agent
agent = create_lc_agent()
result = agent.invoke({'input': 'What are my skills?'})
assert 'output' in result
assert 'search_experience' not in result['output']
print('✓ Agent working')
"

echo ""
echo "✅ All E2E validations passed!"
```

Run validation:
```bash
bash scripts/validate_e2e.sh
```

## Continuous Integration

### GitHub Actions Workflow

The system is designed to support CI/CD. Recommended checks:

1. **Unit tests** on every push
2. **Docker build** validation
3. **Integration tests** in staging environment
4. **Auto-deployment** via webhook

## Related Documentation

- [Vector DB Initialization](./VECTOR_DB_INITIALIZATION.md) - Data pipeline setup
- [Agent Tool Debugging](./AGENT_TOOL_DEBUGGING.md) - Tool invocation troubleshooting
- [MCP Servers](./MCP_SERVERS.md) - Server implementations
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment steps

## Support and Debugging

### Enable Debug Logging

Local development:
```bash
export LOGLEVEL=DEBUG
docker compose up agent
```

Production:
```bash
docker compose logs agent -f --tail=100
```

### Collect Debug Information

```bash
# System info
docker compose ps
docker system df

# Service logs
docker compose logs --tail=200 > debug.log

# Vector DB status
python scripts/init_vector_db.py --check-only >> debug.log

# Agent test
docker compose exec -T agent python -c "from agent.main import create_lc_agent; print(create_lc_agent())" >> debug.log
```

Share `debug.log` for support.
