# MCP Server Setup Guide

## Overview

The Resume Narrator project uses three FastMCP servers to provide specialized tools to the LangChain agent:

1. **Resume PDF Server** (port 9001) - Generates professional PDF resumes
2. **Vector DB Server** (port 9002) - Searches and analyzes professional experience
3. **Code Explorer Server** (port 9003) - Explains system architecture and code

## Architecture

Each MCP server is built with **FastMCP** framework, which provides:
- Built-in HTTP endpoints via `mcp.http_app` (Starlette ASGI app)
- Tool definitions with `@mcp.tool()` decorators
- Custom REST routes with `@mcp.custom_route()` decorators
- Automatic health check endpoints at `/health`

### Server Files

```
mcp-servers/
├── resume_pdf_server.py         # FastMCP server definition
├── vector_db_server.py          # FastMCP server definition
├── code_explorer_server.py      # FastMCP server definition
├── resume_http_server.py        # HTTP wrapper (runs on port 9001)
├── vector_http_server.py        # HTTP wrapper (runs on port 9002)
├── code_http_server.py          # HTTP wrapper (runs on port 9003)
└── server_runner.py             # Orchestrates all servers
```

## Running MCP Servers

### Option 1: Local Development

```bash
# Start all three servers
python mcp-servers/server_runner.py --server all

# Or start a single server
python mcp-servers/server_runner.py --server resume
```

Expected output:
```
Starting all MCP HTTP servers...

  • Starting resume server on port 9001...
  • Starting vector server on port 9002...
  • Starting code server on port 9003...

✓ All servers started

Servers available at:
  • resume: http://localhost:9001
  • vector: http://localhost:9002
  • code: http://localhost:9003

Press Ctrl+C to stop all servers.
```

### Option 2: Docker Compose

```bash
# Start all services including MCP servers
docker compose up --build

# Or just the MCP servers
docker compose up --build mcp-resume mcp-vector mcp-code
```

## Verifying Servers

### Health Check

```bash
# Test each server's health endpoint
curl http://localhost:9001/health
curl http://localhost:9002/health
curl http://localhost:9003/health

# Expected response
{"status": "ok", "service": "resume-pdf-server"}
```

### Test Connectivity

```bash
# Run the test suite
python test_mcp_servers.py

# Expected output
✓ PASS: resume server
✓ PASS: vector server
✓ PASS: code server

✓ All tests passed!
```

### Test Tool Execution

```bash
# Test resume generation endpoint
curl -X POST http://localhost:9001/tool/generate_resume_pdf \
  -H "Content-Type: application/json" \
  -d '{"template": "professional", "sections": ["contact", "experience"]}'

# Test experience search
curl -X POST http://localhost:9002/tool/search_experience \
  -H "Content-Type: application/json" \
  -d '{"query": "Python development"}'

# Test architecture explanation
curl -X POST http://localhost:9003/tool/explain_architecture \
  -H "Content-Type: application/json" \
  -d '{"component": "full_stack"}'
```

## Agent Integration

The agent connects to MCP servers via HTTP endpoints defined in `agent/config.py`:

```python
MCP_RESUME_URL = os.getenv("MCP_RESUME_URL", "http://localhost:9001")
MCP_VECTOR_URL = os.getenv("MCP_VECTOR_URL", "http://localhost:9002")
MCP_CODE_URL = os.getenv("MCP_CODE_URL", "http://localhost:9003")
```

### How Tools Are Called

1. **Agent receives query** → `agent.invoke({"input": "..."})`
2. **LLM decides to use a tool** → Generates AIMessage with tool_calls
3. **Tool is executed** → `generate_resume_pdf()`, `search_experience()`, etc.
4. **Tool makes HTTP request** → `httpx.post("http://localhost:9001/tool/...")`
5. **MCP server handles request** → FastMCP routes to handler function
6. **Result returned** → ToolMessage with execution result
7. **Agent processes result** → Generates final response

## Environment Configuration

### For Docker

The `docker-compose.yml` sets these environment variables for the agent container:

```yaml
environment:
  - MCP_RESUME_URL=http://mcp-resume:9001
  - MCP_VECTOR_URL=http://mcp-vector:9002
  - MCP_CODE_URL=http://mcp-code:9003
```

### For Local Testing

```bash
export MCP_RESUME_URL=http://localhost:9001
export MCP_VECTOR_URL=http://localhost:9002
export MCP_CODE_URL=http://localhost:9003
```

## Troubleshooting

### Servers Not Starting

1. Check port availability:
   ```bash
   lsof -i :9001 -i :9002 -i :9003
   ```

2. Check Python installation:
   ```bash
   python -c "import uvicorn, fastmcp; print('✓ Dependencies OK')"
   ```

3. Check server files exist:
   ```bash
   ls -la mcp-servers/{resume,vector,code}_*.py
   ```

### Connection Refused

If you get "Connection refused" when tools try to call MCP servers:

1. **Verify servers are running**:
   ```bash
   curl -I http://localhost:9001/health
   ```

2. **For Docker**: Check container networking
   ```bash
   docker network ls
   docker compose ps
   docker compose logs mcp-resume
   ```

3. **Check agent config**:
   ```bash
   # Make sure URLs are correct
   python -c "from agent.config import MCP_*; print(MCP_RESUME_URL)"
   ```

### Tool Execution Failures

1. Check MCP server logs for errors
2. Verify tool endpoint exists:
   ```bash
   curl -v -X POST http://localhost:9001/tool/generate_resume_pdf \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

3. Check if dependencies are installed:
   ```bash
   pip install -r mcp-servers/requirements.txt
   ```

## Files Created/Modified

### New Files
- `mcp-servers/resume_http_server.py` - HTTP wrapper for resume server
- `mcp-servers/vector_http_server.py` - HTTP wrapper for vector server
- `mcp-servers/code_http_server.py` - HTTP wrapper for code server
- `mcp-servers/server_runner.py` - Orchestration script
- `test_mcp_servers.py` - Connectivity test suite
- `MCP_SERVER_SETUP.md` - This file

### Configuration
The existing `docker-compose.yml` already references the correct HTTP server files, so no changes were needed there.

## Next Steps

To get the full system running:

1. **Start MCP servers**:
   ```bash
   python mcp-servers/server_runner.py --server all
   ```

2. **In another terminal, start the agent UI**:
   ```bash
   chainlit run agent/ui/chainlit_app.py
   ```

3. **Verify connectivity**:
   ```bash
   python test_mcp_servers.py
   ```

4. **Test with Docker** (when ready):
   ```bash
   docker compose up --build
   ```
