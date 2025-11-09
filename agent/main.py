"""
Resume Narrator Agent using LangChain 1.0
"""
import os
import json
import httpx
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain.agents import create_agent as create_langchain_agent
from langchain_core.messages import HumanMessage
from typing import Any

# Initialize LLM
llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
    base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
)

# MCP server URLs
MCP_RESUME_URL = os.getenv("MCP_RESUME_URL", "http://localhost:9001")
MCP_VECTOR_URL = os.getenv("MCP_VECTOR_URL", "http://localhost:9002")
MCP_CODE_URL = os.getenv("MCP_CODE_URL", "http://localhost:9003")


@tool
def generate_resume_pdf(template: str = "professional", sections: str = "") -> str:
    """Generate a professional PDF resume.

    Args:
        template: Resume template type (e.g., 'professional')
        sections: Comma-separated list of sections to include

    Returns:
        JSON string with resume generation result
    """
    try:
        params = {
            "template": template,
            "sections": sections.split(",") if sections else [],
        }
        response = httpx.post(f"{MCP_RESUME_URL}/tool/generate_resume_pdf", json=params)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def search_experience(query: str) -> str:
    """Search through professional experience and projects.

    Args:
        query: Search query string

    Returns:
        JSON string with search results
    """
    try:
        response = httpx.post(
            f"{MCP_VECTOR_URL}/tool/search_experience", json={"query": query}
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def explain_architecture(component: str = "full_stack") -> str:
    """Explain the architecture of how the chatbot works.

    Args:
        component: Component name (agent, mcp_servers, deployment, or full_stack)

    Returns:
        JSON string with architecture explanation
    """
    try:
        response = httpx.post(
            f"{MCP_CODE_URL}/tool/explain_architecture", json={"component": component}
        )
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def analyze_skills() -> str:
    """Analyze skill coverage across experiences.

    Returns:
        JSON string with skill analysis
    """
    try:
        response = httpx.post(f"{MCP_VECTOR_URL}/tool/analyze_skill_coverage", json={})
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def create_agent() -> Any:
    """Create the LangChain 1.0 agent with tool calling.

    Returns a wrapper that matches the Chainlit interface: invoke({"input": "..."}) -> {"output": "..."}
    """
    tools = [
        generate_resume_pdf,
        search_experience,
        explain_architecture,
        analyze_skills,
    ]

    # Create the agent graph
    graph = create_langchain_agent(
        llm,
        tools,
    )

    # Wrap the graph to match Chainlit's expected interface
    class AgentWrapper:
        """Wrapper to convert between Chainlit interface and LangChain 1.0 agent interface"""

        def __init__(self, graph):
            self.graph = graph

        def invoke(self, input_dict: dict) -> dict:
            """
            Convert from Chainlit interface: {"input": "..."}
            to LangChain agent interface: {"messages": [...]}
            and back.
            """
            user_input = input_dict.get("input", "")

            # Call the agent with the new interface
            result = self.graph.invoke({"messages": [HumanMessage(content=user_input)]})

            # Extract the final response from messages
            messages = result.get("messages", [])
            output = ""
            if messages:
                last_message = messages[-1]
                output = getattr(last_message, "content", str(last_message))

            return {"output": output, "input": user_input}

    return AgentWrapper(graph)


if __name__ == "__main__":
    # Example usage
    agent = create_agent()
    result = agent.invoke({"input": "What are my main skills?"})
    print(result)
