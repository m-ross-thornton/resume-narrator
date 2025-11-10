#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot agent tool access in LangChain/LangGraph.
This helps identify why tools aren't being called by the agent.
"""

import json
import sys
import logging
from pprint import pprint
from agent.main import (
    create_lc_agent,
    generate_resume_pdf,
    search_experience,
    explain_architecture,
    analyze_skills,
)
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Configure logging to see LangChain internal operations
logging.basicConfig(
    level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
)

# Suppress noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def inspect_tools():
    """Inspect the tools to ensure they're properly defined."""
    print_section("Tool Definitions")

    tools = [
        generate_resume_pdf,
        search_experience,
        explain_architecture,
        analyze_skills,
    ]

    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Type: {type(tool)}")
        print(f"  Callable: {callable(tool)}")
        print(f"  Has name: {hasattr(tool, 'name')}")
        print(f"  Has description: {hasattr(tool, 'description')}")
        if hasattr(tool, "args"):
            print(f"  Args schema: {tool.args}")
        print()


def inspect_agent_structure():
    """Inspect the agent graph structure."""
    print_section("Agent Structure")

    agent = create_lc_agent()
    print(f"Agent wrapper type: {type(agent)}")
    print(f"Agent wrapper class: {agent.__class__.__name__}")
    print(f"Has invoke: {hasattr(agent, 'invoke')}")
    print(f"Has agent_graph: {hasattr(agent, 'agent_graph')}")

    if hasattr(agent, "agent_graph"):
        graph = agent.agent_graph
        print(f"\nAgent graph type: {type(graph)}")
        print(f"Agent graph: {graph}")

        # Try to access graph structure
        if hasattr(graph, "nodes"):
            print(f"Graph nodes: {list(graph.nodes)}")
        if hasattr(graph, "edges"):
            print(f"Graph edges: {list(graph.edges)}")

        # Check for tools in the graph
        if hasattr(graph, "get_graph"):
            try:
                print(f"\nGraph structure:")
                print(graph.get_graph())
            except Exception as e:
                print(f"Could not get graph structure: {e}")


def test_agent_with_logging(query: str):
    """Test agent invocation with detailed logging."""
    print_section(f"Agent Invocation Test: '{query}'")

    agent = create_lc_agent()

    print("Step 1: Creating input...")
    input_dict = {"input": query}
    print(f"Input: {input_dict}\n")

    print("Step 2: Getting agent_graph...")
    graph = agent.agent_graph
    print(f"Graph type: {type(graph)}\n")

    print("Step 3: Creating initial state...")
    initial_state = {"messages": [HumanMessage(content=query)]}
    print(f"Initial state messages: {initial_state['messages']}\n")

    print("Step 4: Invoking agent (this may take a while)...\n")
    try:
        result = graph.invoke(initial_state)

        print_section("Agent Execution Result")
        print("Final state messages:")
        if isinstance(result, dict) and "messages" in result:
            for i, msg in enumerate(result["messages"]):
                print(f"\n  Message {i}: {type(msg).__name__}")
                print(f"    Content preview: {str(msg.content)[:200]}")
                if hasattr(msg, "tool_calls"):
                    print(f"    Tool calls: {msg.tool_calls}")
                if isinstance(msg, ToolMessage):
                    print(
                        f"    Tool result: {msg.content[:200] if len(msg.content) > 200 else msg.content}"
                    )

        print("\n\nFull result structure:")
        print(
            json.dumps(
                {
                    k: str(v)[:100] if not isinstance(v, (list, dict)) else str(type(v))
                    for k, v in result.items()
                    if k != "messages"
                },
                indent=2,
            )
        )

    except Exception as e:
        print(f"ERROR during agent execution: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()


def check_llm_model():
    """Check if the LLM model supports tool calling."""
    print_section("LLM Configuration Check")

    from agent.config import OLLAMA_MODEL, OLLAMA_HOST
    from langchain_ollama import ChatOllama

    print(f"Model: {OLLAMA_MODEL}")
    print(f"Host: {OLLAMA_HOST}")

    try:
        llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_HOST)
        print(f"LLM type: {type(llm)}")
        print(f"Can bind tools: {hasattr(llm, 'bind_tools')}")

        # Try binding tools
        tools = [generate_resume_pdf, search_experience]
        try:
            bound_llm = llm.bind_tools(tools)
            print(f"Successfully bound {len(tools)} tools to LLM")
        except Exception as e:
            print(f"ERROR binding tools: {e}")

    except Exception as e:
        print(f"ERROR creating LLM: {e}")
        print("Note: This is expected if Ollama is not running")


def main():
    """Run all diagnostics."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  LangChain Agent Tool Debugging Diagnostics".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")

    # Run diagnostics
    inspect_tools()
    check_llm_model()
    inspect_agent_structure()

    # Test with a simple query
    test_agent_with_logging("What can you help me with?")

    print_section("Diagnostics Complete")
    print("\nKey things to check in the output above:")
    print("  1. Are all 4 tools properly defined and callable?")
    print("  2. Does the agent graph have the tools bound?")
    print("  3. Are there ToolMessage or AIMessage with tool_calls in the result?")
    print("  4. Is the LLM able to bind tools (requires tool-calling support)?")
    print("  5. Are tool execution logs visible in the messages?")


if __name__ == "__main__":
    main()
