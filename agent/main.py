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
        logger.info(
            f"generate_resume called with template='{template}', sections='{sections}'"
        )
        params = {
            "template": template,
            "sections": sections.split(",") if sections else [],
        }
        logger.debug(
            f"generate_resume sending request to {MCP_RESUME_URL}/tool/generate_resume with params: {params}"
        )
        response = httpx.post(
            f"{MCP_RESUME_URL}/tool/generate_resume", json=params, timeout=30.0
        )
        logger.debug(f"generate_resume response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        logger.info(
            f"generate_resume completed successfully, response keys: {result.keys() if isinstance(result, dict) else 'not a dict'}"
        )
        return json.dumps(result)
    except httpx.TimeoutException as e:
        logger.error(f"generate_resume timeout: {e}")
        return json.dumps({"error": f"timeout: {str(e)}"})
    except Exception as e:
        logger.error(f"generate_resume error: {e}", exc_info=True)
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
        logger.info(f"search_experience called with query='{query}'")
        logger.debug(
            f"search_experience sending request to {MCP_VECTOR_URL}/tool/search_experience"
        )
        response = httpx.post(
            f"{MCP_VECTOR_URL}/tool/search_experience",
            json={"query": query},
            timeout=30.0,
        )
        logger.debug(f"search_experience response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        logger.info(
            f"search_experience completed successfully, found {len(result) if isinstance(result, list) else 'results'}"
        )
        return json.dumps(result)
    except httpx.TimeoutException as e:
        logger.error(f"search_experience timeout: {e}")
        return json.dumps({"error": f"timeout: {str(e)}"})
    except Exception as e:
        logger.error(f"search_experience error: {e}", exc_info=True)
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
        logger.info(f"explain_architecture called with component='{component}'")
        logger.debug(
            f"explain_architecture sending request to {MCP_CODE_URL}/tool/explain_architecture"
        )
        response = httpx.post(
            f"{MCP_CODE_URL}/tool/explain_architecture",
            json={"component": component},
            timeout=30.0,
        )
        logger.debug(f"explain_architecture response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        logger.info(f"explain_architecture completed successfully")
        return json.dumps(result)
    except httpx.TimeoutException as e:
        logger.error(f"explain_architecture timeout: {e}")
        return json.dumps({"error": f"timeout: {str(e)}"})
    except Exception as e:
        logger.error(f"explain_architecture error: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


@tool
def analyze_skills() -> str:
    """Analyze skill coverage across experiences.

    Returns:
        JSON string with skill analysis
    """
    try:
        logger.info("analyze_skills called")
        logger.debug(
            f"analyze_skills sending request to {MCP_VECTOR_URL}/tool/analyze_skill_coverage"
        )
        response = httpx.post(
            f"{MCP_VECTOR_URL}/tool/analyze_skill_coverage", json={}, timeout=30.0
        )
        logger.debug(f"analyze_skills response status: {response.status_code}")
        response.raise_for_status()
        result = response.json()
        logger.info("analyze_skills completed successfully")
        return json.dumps(result)
    except httpx.TimeoutException as e:
        logger.error(f"analyze_skills timeout: {e}")
        return json.dumps({"error": f"timeout: {str(e)}"})
    except Exception as e:
        logger.error(f"analyze_skills error: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


def create_lc_agent() -> Any:
    """Create the Resume Narrator agent with proper tool invocation."""
    logger.info("Creating LangChain agent...")
    logger.info(f"Using Ollama model: {OLLAMA_MODEL}")
    logger.info(f"Ollama host: {OLLAMA_HOST}")
    logger.info(f"MCP Resume URL: {MCP_RESUME_URL}")
    logger.info(f"MCP Vector URL: {MCP_VECTOR_URL}")
    logger.info(f"MCP Code URL: {MCP_CODE_URL}")

    tools = [generate_resume, search_experience, explain_architecture, analyze_skills]
    logger.info(f"Binding {len(tools)} tools to agent: {[t.name for t in tools]}")

    # Initialize LLM with configured settings
    logger.debug("Initializing ChatOllama LLM...")
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0.3,
        num_predict=512,  # Generate up to 512 tokens instead of default
        repeat_penalty=1.1,  # Penalize repetition
        top_k=40,  # Top-k sampling
        top_p=0.9,  # Top-p (nucleus) sampling
        num_ctx=4096,  # Ensure adequate context window
    )
    logger.debug("ChatOllama LLM initialized successfully")
    logger.info(f"LLM model: {llm.model}")
    logger.info(f"LLM base_url: {llm.base_url}")
    logger.info(f"LLM temperature: {llm.temperature}")

    logger.debug("Creating agent with LangChain create_agent...")
    agent = create_agent(
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    logger.info("Agent created successfully")
    logger.debug(f"Agent has astream_events: {hasattr(agent, 'astream_events')}")
    logger.debug(f"Agent has invoke: {hasattr(agent, 'invoke')}")
    return agent


if __name__ == "__main__":
    # Debug: Test ChatOllama directly without agent wrapper
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Enable httpx logging to see actual HTTP requests
    logging.getLogger("httpx").setLevel(logging.DEBUG)

    print("\n=== Testing ChatOllama directly (no agent wrapper) ===")
    print(f"OLLAMA_HOST: {OLLAMA_HOST}")
    print(f"OLLAMA_MODEL: {OLLAMA_MODEL}")

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0.3,
        num_predict=512,
        repeat_penalty=1.1,
        top_k=40,
        top_p=0.9,
        num_ctx=4096,
    )
    print(f"ChatOllama model: {llm.model}")
    print(f"ChatOllama base_url: {llm.base_url}")

    # Check what parameters are actually stored
    for attr in [
        "temperature",
        "num_predict",
        "repeat_penalty",
        "top_k",
        "top_p",
        "num_ctx",
    ]:
        if hasattr(llm, attr):
            print(f"ChatOllama {attr}: {getattr(llm, attr)}")

    print("\nTest 1: Simple string prompt")
    response = llm.invoke("Who are you and what is your background?")
    print(f"Response length: {len(response.content)} chars")
    print(f"Response: {response.content[:200]}")
    if hasattr(response, "response_metadata"):
        print(f"Metadata: {response.response_metadata}")

    print("\nTest 2: Using messages format")
    from langchain_core.messages import HumanMessage, SystemMessage

    messages = [
        SystemMessage(
            content="You are a helpful AI assistant. Provide detailed, comprehensive responses."
        ),
        HumanMessage(content="Who are you and what is your background?"),
    ]
    response2 = llm.invoke(messages)
    print(f"Response length: {len(response2.content)} chars")
    print(f"Response: {response2.content[:200]}")
    if hasattr(response2, "response_metadata"):
        print(f"Metadata: {response2.response_metadata}")

    print("\n=== Testing with agent wrapper ===")
    agent = create_lc_agent()
    result = agent.invoke(
        HumanMessage(content="Who are you and what is your background?")
    )
    print(f"Agent result type: {type(result)}")
    print(f"Agent result: {result}")
