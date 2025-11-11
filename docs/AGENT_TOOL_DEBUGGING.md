# Agent Tool Calling - Debugging & Troubleshooting

## Overview

The Resume Narrator agent uses LangGraph's `create_react_agent` with Ollama (llama3.1) to answer questions about your professional background by invoking tools to search experience data, generate resumes, and explain system architecture.

## How It Should Work

```
User Question
    ↓
Agent analyzes question
    ↓
Agent identifies relevant tools
    ↓
Agent invokes tools with proper function calling
    ↓
Tools execute and return results
    ↓
Agent formulates response based on tool results
    ↓
Response returned to user
```

## Common Issues

### Issue: Agent outputs tool call syntax instead of executing tools

**Example:**
```
User: "What are my main skills?"
Agent Response: "search_experience(query='skills')"
```

Instead of actually calling the tool and returning results.

### Root Causes

1. **Ollama Function Calling Limitation**: The llama3.1 model may not properly support LangChain's function calling protocol
2. **Tool Binding Issue**: Tools may not be properly bound to the model
3. **Context/Prompt Issue**: The system prompt may not be guiding the model to use tools correctly
4. **Configuration Issue**: Model parameters may need tuning for better tool usage

## Debugging Steps

### 1. Check Agent Logs

When running in Docker, check the agent container logs for tool invocation details:

```bash
# View agent logs
docker compose logs agent -f

# Look for these debug messages:
# - "Agent returned X messages"
# - "Last message type: AIMessage"
# - "Warning: Agent output contains tool call syntax"
```

The logging includes:
- Number of messages in the agent state
- Type of the final message (should be `AIMessage`)
- Preview of the output content
- Warnings if tool call syntax is detected instead of actual results

### 2. Check Tool Binding

The agent now explicitly binds tools using `.bind_tools()`:

```python
llm_with_tools = llm.bind_tools(tools)
agent = create_react_agent(llm_with_tools, tools)
```

This tells Ollama which tools are available and their signatures.

### 3. Verify Tool Configuration

Ensure the tool definitions are correct:

```python
@tool
def search_experience(query: str) -> str:
    """Search through professional experience and projects.

    Args:
        query: Search query string

    Returns:
        JSON string with search results
    """
    # Implementation...
```

Each tool needs:
- Clear docstring explaining its purpose
- Well-defined parameters with type hints
- Documented return value

### 4. Check MCP Server Availability

Tools make HTTP calls to MCP servers. Ensure they're running:

```bash
# Check if MCP servers are healthy
curl http://localhost:9001/health  # Resume server
curl http://localhost:9002/health  # Vector server
curl http://localhost:9003/health  # Code server

# Or in Docker
docker compose exec agent curl http://mcp-resume:9001/health
docker compose exec agent curl http://mcp-vector:9002/health
docker compose exec agent curl http://mcp-code:9003/health
```

### 5. Test Agent Directly

```bash
# In the agent container
python -c "
from agent.main import create_lc_agent
agent = create_lc_agent()
result = agent.invoke({'input': 'What are my main skills?'})
print('Result:', result)
"
```

Check the output for:
- Tool invocations (you should see evidence of tool calls)
- Actual results from tools (not just syntax)
- Error messages

## Solutions

### Solution 1: Improve System Prompt

The system prompt now includes explicit tool usage instructions:

```
DO:
- Always call tools first before providing any professional profile information
- Use search_experience for work history, skills, and project questions
- Use analyze_skills to provide comprehensive skill assessments
- Use generate_resume_pdf when explicitly asked for a resume or CV
- Use explain_architecture when asked about how this chatbot works

DO NOT:
- Make up information if you don't have it
- Skip calling tools when they would provide relevant information
```

These instructions are in `agent/config.py` in the `SYSTEM_PROMPT` variable.

### Solution 2: Adjust Ollama Model Parameters

If tools still aren't being invoked properly, try adjusting parameters in `agent/main.py`:

```python
llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_HOST,
    temperature=0.1,  # Lower temperature for more deterministic tool calling
    num_ctx=4096,     # Larger context window
    num_predict=2048, # Max tokens for response
    top_k=40,         # Nucleus sampling
    top_p=0.9,        # Top-p sampling
)
```

Lower `temperature` (0.1-0.3) makes the model more deterministic and more likely to follow instructions like using tools.

### Solution 3: Check MCP Tool Endpoints

Verify the tools are accessible and returning proper results:

```bash
# Test search_experience endpoint
curl -X POST http://localhost:9002/tool/search_experience \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning"}'

# Test analyze_skills endpoint
curl -X POST http://localhost:9002/tool/analyze_skill_coverage \
  -H "Content-Type: application/json" \
  -d '{}'
```

If these return errors, the tools won't work even if the agent invokes them properly.

### Solution 4: Fallback to Simpler Agent (if needed)

If function calling remains problematic, we could implement a simpler agent that:
1. Uses the model to generate text
2. Parses tool call syntax from the text
3. Executes the tools based on parsed calls
4. Feeds results back to the agent

This would be less ideal but would work with any LLM.

## Architecture Details

### Tool Invocation Flow

```
1. User sends message
   ↓
2. create_react_agent (LangGraph)
   ├─ Passes message to LLM with bound tools
   ├─ LLM decides if tools are needed
   ├─ If yes, generates tool calls
   ├─ Agent executes tool calls
   ├─ Receives results
   ├─ Passes results back to LLM
   └─ LLM formulates final response

3. Response returned to user
```

### Key Components

- **LLM**: ChatOllama with llama3.1 model
- **Tools**: 4 @tool decorated functions
- **Tool Binding**: `.bind_tools()` adds tool knowledge to LLM
- **Agent**: `create_react_agent` from LangGraph handles the ReAct loop
- **MCP Servers**: HTTP endpoints that tools call to get data

## Testing Tool Invocation

### Unit Test Tools Directly

```python
from agent.main import search_experience

result = search_experience(query="machine learning")
print(result)  # Should return JSON with search results
```

### Integration Test Full Agent

```python
from agent.main import create_lc_agent

agent = create_lc_agent()

# Test that requires tool usage
result = agent.invoke({'input': 'What AI projects have I worked on?'})
print(result['output'])

# Should contain actual project information, not just syntax
```

## Performance Considerations

### Context Window

Larger context windows allow more tool interactions:
- `num_ctx=2048`: Default, fast but limited
- `num_ctx=4096`: Moderate, good balance
- `num_ctx=8192`: Large, slow but more capability

### Temperature

- `temperature=0.0`: Deterministic, always same output
- `temperature=0.3`: Low randomness, good for tasks
- `temperature=0.7`: Moderate randomness
- `temperature=1.0`: Max randomness

For reliable tool calling, use lower temperatures (0.1-0.3).

## Expected Behavior

When working correctly, the agent should:

✓ Receive user question
✓ Determine if tools are needed
✓ Invoke appropriate tools
✓ Use tool results in response
✓ Provide factual, detailed answers about your experience
✓ Never make up information

❌ Should NOT:
✗ Output tool call syntax as response
✗ Say "I don't have information" when tools could provide it
✗ Return raw JSON from tools
✗ Make up fake experience details

## Monitoring

### Enable Debug Logging

In the agent or in Chainlit startup:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This enables the debug messages from the agent that show:
- Message flow through the agent
- Tool binding status
- Final message extraction

### Monitor MCP Server Health

```bash
# Periodic health checks
while true; do
  curl -s http://localhost:9002/health | jq .
  sleep 5
done
```

## Related Documentation

- [Agent Architecture](./docs/Agent_Architecture.md) - Full system design
- [MCP Servers](./docs/MCP_Servers.md) - Tool implementations
- [Vector DB](./docs/VECTOR_DB_INITIALIZATION.md) - Experience data backend
- [System Prompt](./agent/config.py) - Tool instructions

## Troubleshooting Checklist

- [ ] Agent logs show tool invocation attempts
- [ ] MCP servers are running and healthy
- [ ] Tool endpoints are accessible and returning data
- [ ] System prompt includes tool usage instructions
- [ ] Model parameters are configured (low temperature)
- [ ] Tools are properly decorated with @tool
- [ ] Tool docstrings are clear and detailed
- [ ] Tool return types match expectations (usually JSON strings)

## Quick Fix Checklist

1. **Check logs**: `docker compose logs agent -f`
2. **Verify MCP servers**: `curl http://localhost:9002/health`
3. **Test tools directly**: `curl -X POST http://localhost:9002/tool/...`
4. **Restart agent**: `docker compose restart agent`
5. **Rebuild if code changed**: `docker compose up -d --build agent`
6. **Check system prompt**: Make sure tool instructions are present in `SYSTEM_PROMPT`

## Getting Help

If tools still aren't being invoked:

1. Collect logs: `docker compose logs agent > agent.log`
2. Run direct test: Show output from `python -c "from agent.main import create_lc_agent; agent.invoke(...)"`
3. Check MCP endpoints: Show `curl -X POST http://localhost:9002/tool/...` output
4. Provide details about the failing query and expected vs actual behavior
