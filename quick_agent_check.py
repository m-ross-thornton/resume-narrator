#!/usr/bin/env python3
"""
Quick check of agent and tool structure without requiring Ollama.
"""

import sys
from agent.main import (
    generate_resume_pdf,
    search_experience,
    explain_architecture,
    analyze_skills,
)


def check_tools():
    """Verify all tools are properly defined as @tool objects."""
    print("\n" + "=" * 80)
    print("TOOL STRUCTURE CHECK")
    print("=" * 80 + "\n")

    tools = {
        "generate_resume_pdf": generate_resume_pdf,
        "search_experience": search_experience,
        "explain_architecture": explain_architecture,
        "analyze_skills": analyze_skills,
    }

    for name, tool in tools.items():
        print(f"Tool: {name}")
        print(f"  Type: {type(tool).__name__}")
        print(f"  Module: {type(tool).__module__}")
        print(f"  Has 'name' attr: {hasattr(tool, 'name')}")
        if hasattr(tool, "name"):
            print(f"    name = '{tool.name}'")
        print(f"  Has 'description' attr: {hasattr(tool, 'description')}")
        if hasattr(tool, "description"):
            desc = tool.description
            print(
                f"    description = '{desc[:100]}...' (truncated)"
                if len(desc) > 100
                else f"    description = '{desc}'"
            )
        print(f"  Has 'args' attr: {hasattr(tool, 'args')}")
        if hasattr(tool, "args"):
            print(f"    args = {tool.args}")
        print(f"  Callable: {callable(tool)}")
        print()


def check_agent():
    """Check agent creation without invoking it."""
    print("\n" + "=" * 80)
    print("AGENT CREATION CHECK (No Ollama Required)")
    print("=" * 80 + "\n")

    try:
        from agent.main import create_lc_agent

        print("✓ Successfully imported create_lc_agent")

        # This will fail if Ollama is not running, but we can check the structure
        print("\nAttempting to create agent...")
        try:
            agent = create_lc_agent()
            print("✓ Agent created successfully")
            print(f"  Type: {type(agent).__name__}")
            print(f"  Has invoke: {hasattr(agent, 'invoke')}")
            print(f"  Has agent_graph: {hasattr(agent, 'agent_graph')}")

            if hasattr(agent, "agent_graph"):
                graph = agent.agent_graph
                print(f"  Graph type: {type(graph).__name__}")

                # Try to inspect the graph
                try:
                    if hasattr(graph, "nodes"):
                        print(f"  Graph nodes: {list(graph.nodes.keys())}")
                    if hasattr(graph, "edges"):
                        edges = list(graph.edges)
                        print(f"  Graph edges: {edges}")
                except Exception as e:
                    print(f"  Could not inspect graph nodes/edges: {e}")

        except ImportError as e:
            print(f"✗ Import error: {e}")
        except Exception as e:
            if "Connection refused" in str(e) or "connect" in str(e).lower():
                print(
                    f"⚠ Agent creation requires Ollama (expected error): {type(e).__name__}"
                )
                print(f"  Message: {str(e)[:100]}")
            else:
                print(f"✗ Error creating agent: {e}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()


def check_imports():
    """Check all required imports."""
    print("\n" + "=" * 80)
    print("IMPORT CHECKS")
    print("=" * 80 + "\n")

    imports_to_check = [
        ("langchain_ollama", "ChatOllama"),
        ("langchain.tools", "tool"),
        ("langchain.agents", "create_agent"),
        ("langchain_core.messages", "HumanMessage"),
        ("agent.config", "OLLAMA_MODEL"),
    ]

    for module, item in imports_to_check:
        try:
            mod = __import__(module, fromlist=[item])
            obj = getattr(mod, item)
            print(f"✓ {module}.{item}")
        except ImportError as e:
            print(f"✗ {module}.{item} - {e}")
        except AttributeError as e:
            print(f"✗ {module}.{item} - {e}")


def main():
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + "  Agent and Tool Structure Quick Check".center(78) + "║")
    print("╚" + "=" * 78 + "╝")

    check_imports()
    check_tools()
    check_agent()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nUse this output to answer these questions:")
    print("  1. Are all 4 tools defined as @tool decorated functions?")
    print("  2. Do all tools have 'name' and 'description' attributes?")
    print("  3. Can the agent be created (if Ollama is running)?")
    print("  4. Does the agent have an agent_graph attribute?")
    print("  5. Are all imports working correctly?")
    print(
        "\nIf Ollama is not running, the agent creation will fail with a Connection error."
    )
    print("That's expected. Focus on whether the structure looks correct.\n")


if __name__ == "__main__":
    main()
