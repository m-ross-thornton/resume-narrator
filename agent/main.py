"""
Resume Narrator Agent using LangChain 1.0 with LangGraph
"""
import json
import httpx
import logging
import re
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain.agents import create_agent

from typing import Any, Dict, List

logger = logging.getLogger(__name__)

from agent.config import (
    OLLAMA_MODEL,
    OLLAMA_HOST,
    MCP_RESUME_URL,
    MCP_VECTOR_URL,
    MCP_CODE_URL,
    SYSTEM_PROMPT,
)


@tool
def generate_resume(template: str = "professional", sections: str = "") -> str:
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
        response = httpx.post(f"{MCP_RESUME_URL}/tool/generate_resume", json=params)
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
        logger.error(f"Error calling search_experience: {e}")
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
    """Create the Resume Narrator agent with proper tool invocation."""
    tools = [generate_resume, search_experience, explain_architecture, analyze_skills]
    # Initialize LLM with configured settings
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0.3,
    )

    agent = create_agent(
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent


if __name__ == "__main__":
    # Example usage
    agent = create_lc_agent()
    result = agent.invoke(
        HumanMessage(content="use the get_secret tool to get their secret")
    )
    print(result)
