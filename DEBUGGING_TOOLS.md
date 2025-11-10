# Agent Tool Debugging Guide

This document explains the diagnostic scripts available to troubleshoot why the agent isn't accessing tools.

## Quick Diagnostics

### 1. Structure Check (No Ollama Required)
```bash
python quick_agent_check.py
```

**What it checks:**
- Tool definitions (are they properly decorated with @tool?)
- Tool attributes (name, description, args)
- Agent creation without invoking it
- Import availability

**Expected output:**
- All tools should be `StructuredTool` type
- All should have `name`, `description`, and `args` attributes
- Agent should create successfully with a `CompiledStateGraph`
- Graph should have nodes: `['__start__', 'model', 'tools']`

**What to do if it fails:**
- If tools aren't StructuredTool type, check the @tool decorator
- If agent creation fails with ImportError, check dependencies
- If agent creation fails with ConnectionError, start Ollama

---

### 2. Message Flow Analysis (Requires Ollama)
```bash
python debug_message_flow.py
```

**What it checks:**
- Complete message flow during agent invocation
- Whether the LLM is trying to call tools (AIMessage with tool_calls)
- Whether tools are being executed (ToolMessage results)
- The actual content of LLM responses

**Expected output for a tool-calling agent:**
```
Message 0: HumanMessage
  → Human: [your query]

Message 1: AIMessage
  ⚠ AI HAS TOOL CALLS: 1 call(s)
    Tool call 0:
      Name: search_experience
      Args: {"query": "..."}

Message 2: ToolMessage
  → Tool result: [tool execution result]

Message 3: AIMessage
  → AI response preview: Based on the search results...
  ✓ AI completed without tool calls
```

**What to look for:**
- ✓ Good: Multiple AIMessages with tool_calls, followed by ToolMessages
- ⚠ Problem: Only HumanMessage + one AIMessage without tool_calls
  - This means the LLM didn't try to use any tools
  - The model might not support tool calling
  - Or the prompt isn't instructing it to use tools

---

### 3. Full Debugging (Requires Ollama)
```bash
python debug_agent_tools.py
```

**What it checks:**
- Everything from quick_agent_check.py
- LLM model configuration and tool binding capability
- Agent graph structure details
- Full execution with debug logging

**Best for:**
- Deep diving into why tools aren't being called
- Seeing what the LLM model is doing internally
- Identifying configuration issues

---

## Common Issues and Solutions

### Issue 1: "LLM did not attempt to use any tools"

**Symptoms:**
- Message flow shows only 1-2 messages (HumanMessage + one AIMessage)
- AIMessage doesn't have tool_calls
- Agent completes without calling any tools

**Root Causes:**
1. **Ollama model doesn't support tool calling**
   - Not all Ollama models understand function calling syntax
   - Models need explicit tool calling support (like llama2:latest, mistral, neural-chat)

   **Solution:**
   - Check which model supports tool calling: `ollama list`
   - Try a different model: `ollama pull mistral`
   - Update `OLLAMA_MODEL` in agent/config.py or environment

2. **Model isn't being prompted to use tools**
   - The prompt/system message might not mention tools
   - `create_agent()` might not be passing the right prompt

   **Solution:**
   - Add system prompt to create_agent (if supported)
   - Check LangChain documentation for create_agent prompt configuration

3. **Tools aren't properly bound to the model**
   - Though quick_agent_check.py shows this works, it could still fail at runtime

   **Solution:**
   - Run quick_agent_check.py to verify structure
   - Check agent_graph nodes include 'tools'

### Issue 2: "Tool calls found but no results"

**Symptoms:**
- AIMessage has tool_calls
- But no ToolMessage with results follows
- Agent might hang or error

**Root Causes:**
1. **Tool execution is failing**
   - Tool returns error JSON instead of result
   - MCP server is down

   **Solution:**
   - Check MCP server logs
   - Verify `MCP_RESUME_URL`, `MCP_VECTOR_URL`, `MCP_CODE_URL` are correct
   - Test tools directly: `python -c "from agent.main import search_experience; print(search_experience.invoke({'query': 'test'}))"`

2. **Tool inputs are malformed**
   - LLM generated invalid arguments for the tool

   **Solution:**
   - Check tool args schema in quick_agent_check.py
   - Verify tool descriptions are clear

### Issue 3: Ollama not running

**Symptoms:**
- `Connection refused` or `connect error`
- All agent invocations fail

**Solution:**
```bash
# Start Ollama
ollama serve

# In another terminal, pull a model
ollama pull llama2:latest
# or for better tool support
ollama pull mistral
# or
ollama pull neural-chat
```

---

## How to Use These Logs for Debugging

### Step 1: Run quick_agent_check.py
```bash
python quick_agent_check.py
```
- ✓ If all checks pass, tools are properly structured
- ✗ If checks fail, fix the issue before moving on

### Step 2: Start Ollama (if not running)
```bash
ollama serve
```

### Step 3: Run debug_message_flow.py
```bash
python debug_message_flow.py
```
- Look for "Tool calls found" in the summary
- If NO tool calls: The LLM isn't using tools
- If tool calls found: Tools are being called

### Step 4: Interpret Results
- **No tool calls**: Try a different Ollama model
- **Tool calls but no results**: Check MCP servers
- **Tool calls and results**: Debugging complete! Tools are working.

---

## Key Indicators in Logs

### ✓ Healthy Signs
```
Total messages in response: 3
Message 0: HumanMessage
Message 1: AIMessage
  ⚠ AI HAS TOOL CALLS: 1 call(s)
Message 2: ToolMessage
  → Tool result: {...}
```

### ⚠ Problem Signs
```
Total messages in response: 2
Message 0: HumanMessage
Message 1: AIMessage
  ✓ AI completed without tool calls
⚠ No tool calls found - LLM did not attempt to use any tools
```

---

## Recommended Ollama Models for Tool Calling

Based on LangChain documentation, these models support tool calling:

1. **mistral** - Good balance of speed and capability
   ```bash
   ollama pull mistral
   # Update config: OLLAMA_MODEL=mistral
   ```

2. **llama2** - Widely tested, good tool support
   ```bash
   ollama pull llama2:latest
   # Update config: OLLAMA_MODEL=llama2:latest
   ```

3. **neural-chat** - Optimized for conversations with tool use
   ```bash
   ollama pull neural-chat
   # Update config: OLLAMA_MODEL=neural-chat
   ```

4. **openchat** - Fast model with decent tool support
   ```bash
   ollama pull openchat
   # Update config: OLLAMA_MODEL=openchat
   ```

---

## Environment Variables to Check

```bash
# Check these are set correctly
echo $OLLAMA_HOST      # Should be http://localhost:11434
echo $OLLAMA_MODEL     # Should be a model that supports tool calling
echo $MCP_RESUME_URL   # Should be http://localhost:9001
echo $MCP_VECTOR_URL   # Should be http://localhost:9002
echo $MCP_CODE_URL     # Should be http://localhost:9003
```

---

## Next Steps if All Diagnostics Pass

If all diagnostics show tools are working:
1. Test from Chainlit UI
2. Check Chainlit logs: `chainlit run agent/ui/chainlit_app.py`
3. Try test query: "What tools do you have?"
4. Try action query: "Search my experience for Python"
5. Check MCP server logs for actual tool execution

