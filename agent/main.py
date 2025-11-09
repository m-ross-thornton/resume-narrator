"""
Resume Narrator Agent using LangChain 1.0
"""
import json
import httpx
from langchain_ollama import ChatOllama
from langchain.tools import tool
from typing import Any

from agent.config import (
    OLLAMA_MODEL,
    OLLAMA_HOST,
    MCP_RESUME_URL,
    MCP_VECTOR_URL,
    MCP_CODE_URL,
)


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


def create_lc_agent() -> Any:
    """Create the LangChain 1.0 agent with tool calling.

    Returns a runnable that can be invoked with {"input": "..."}.
    """
    # Initialize LLM with configured settings
    agent = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
    ).bind_tools(
        [
            generate_resume_pdf,
            search_experience,
            explain_architecture,
            analyze_skills,
        ]
    )
    return agent


if __name__ == "__main__":
    # Example usage
    agent = create_lc_agent()
    result = agent.invoke({"input": "What are my main skills?"})
    print(result)
