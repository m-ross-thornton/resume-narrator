#!/usr/bin/env python3
"""
Debug agent message flow to see what the LLM is generating.
This helps identify if the LLM is actually trying to call tools.
"""

import sys
import logging
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from agent.main import create_lc_agent

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def analyze_message_flow(query: str):
    """Invoke agent and analyze the complete message flow."""
    print("\n" + "=" * 80)
    print(f"Testing Query: '{query}'")
    print("=" * 80 + "\n")

    try:
        agent = create_lc_agent()
        graph = agent.agent_graph

        print("Step 1: Initial State")
        print("-" * 40)
        initial_state = {"messages": [HumanMessage(content=query)]}
        print(f"Input message: {initial_state['messages'][0].content}\n")

        print("Step 2: Invoking Agent (this will take a moment)...")
        print("-" * 40)
        result = graph.invoke(initial_state)

        print("\nStep 3: Analyzing Results")
        print("-" * 40)

        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            print(f"Total messages in response: {len(messages)}\n")

            for i, msg in enumerate(messages):
                print(f"\nMessage {i}: {type(msg).__name__}")
                print(f"  {'Content length: ' + str(len(msg.content))}")

                if isinstance(msg, HumanMessage):
                    print(f"  → Human: {msg.content}")

                elif isinstance(msg, AIMessage):
                    print(f"  → AI response preview: {msg.content[:200]}")
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        print(f"  ⚠ AI HAS TOOL CALLS: {len(msg.tool_calls)} call(s)")
                        for j, tool_call in enumerate(msg.tool_calls):
                            print(f"    Tool call {j}:")
                            print(f"      Name: {tool_call.get('name', 'N/A')}")
                            print(f"      Args: {tool_call.get('args', {})}")
                    else:
                        print(f"  ✓ AI completed without tool calls")

                elif isinstance(msg, ToolMessage):
                    print(f"  → Tool result: {msg.content[:200]}")
                    print(
                        f"    Tool name: {msg.tool_name if hasattr(msg, 'tool_name') else 'N/A'}"
                    )
                    print(
                        f"    Tool call ID: {msg.tool_call_id if hasattr(msg, 'tool_call_id') else 'N/A'}"
                    )

                else:
                    print(f"  → {type(msg).__name__}: {str(msg.content)[:200]}")

        print("\n\nStep 4: Detailed Analysis")
        print("-" * 40)

        # Check if any tool calls were made
        tool_calls_found = False
        tool_results_found = False

        for msg in result.get("messages", []):
            if (
                isinstance(msg, AIMessage)
                and hasattr(msg, "tool_calls")
                and msg.tool_calls
            ):
                tool_calls_found = True
                print(f"✓ Found AI message with tool calls")
            if isinstance(msg, ToolMessage):
                tool_results_found = True
                print(f"✓ Found tool execution result")

        if not tool_calls_found:
            print("⚠ No tool calls found - LLM did not attempt to use any tools")
            print("  This might mean:")
            print("    1. The LLM model doesn't support tool calling")
            print("    2. The prompt doesn't instruct the LLM to use tools")
            print("    3. The LLM decided not to use tools for this query")

        if tool_calls_found and not tool_results_found:
            print("⚠ Tool calls were made but no results found")
            print("  This might mean the tool execution failed")

        if tool_results_found:
            print("✓ Tools were called and executed successfully")

        return {
            "messages": result.get("messages", []),
            "tool_calls_found": tool_calls_found,
            "tool_results_found": tool_results_found,
        }

    except Exception as e:
        print(f"\n✗ Error during agent execution: {type(e).__name__}")
        print(f"  Message: {e}")
        if "Connection refused" in str(e):
            print("  → This suggests Ollama is not running")
            print("  → Start Ollama with: ollama serve")
        import traceback

        traceback.print_exc()
        return None


def main():
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + "  Agent Message Flow Debugging".center(78) + "║")
    print("╚" + "=" * 78 + "╝")

    # Test different types of queries
    test_queries = [
        "What can you help me with?",
        "Tell me about my skills",
        "Show my resume",
        "Search my experience for Python",
    ]

    results = []
    for query in test_queries:
        result = analyze_message_flow(query)
        if result:
            results.append(result)
        print("\n" + "=" * 80 + "\n")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY OF ALL TESTS")
    print("=" * 80 + "\n")

    for i, (query, result) in enumerate(zip(test_queries[: len(results)], results)):
        print(f"Query {i+1}: {query}")
        print(f"  Tool calls found: {result['tool_calls_found']}")
        print(f"  Tool results found: {result['tool_results_found']}")
        print()

    print("\nKey Observations:")
    print("  • If no tool calls are found in any query, the LLM may not be")
    print("    configured to understand tool calling syntax")
    print("  • Check if the Ollama model supports tool calling")
    print("  • Some Ollama models may need special prompting")


if __name__ == "__main__":
    main()
