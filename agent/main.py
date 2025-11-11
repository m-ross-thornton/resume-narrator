"""
Resume Narrator Agent using LangChain 1.0 with LangGraph
"""
import json
import httpx
from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from typing import Any

from agent.config import (
    OLLAMA_MODEL,
    OLLAMA_HOST,
    MCP_RESUME_URL,
    MCP_VECTOR_URL,
    MCP_CODE_URL,
    SYSTEM_PROMPT,
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
    """Create the LangChain 1.0 ReAct agent with tool calling via LangGraph.

    Returns an agent that accepts {"input": "..."} and returns {"output": "..."}.
    The agent automatically executes tools in a loop until it has a final answer.
    """
    # Initialize LLM with configured settings
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0.3,
    )

    # Define tools
    tools = [
        generate_resume_pdf,
        search_experience,
        explain_architecture,
        analyze_skills,
    ]

    # Create agent using LangGraph's create_react_agent
    # This properly binds tools to the LLM for tool calling
    # The ReAct agent will automatically loop until it has a final answer
    agent = create_react_agent(llm, tools)

    # Wrapper to convert dict input format expected by Chainlit
    class AgentWrapper:
        def __init__(self, agent_graph):
            self.agent_graph = agent_graph

        def invoke(self, input_dict: dict) -> dict:
            """Invoke agent with user input and return response.

            Args:
                input_dict: Dict with "input" key containing user message

            Returns:
                Dict with "output" key containing agent response
            """
            user_input = input_dict.get("input", "")

            # Create initial state with messages for the graph
            # The create_react_agent expects messages in the state
            initial_state = {
                "messages": [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user_input),
                ]
            }

            # Invoke agent - it will execute tools as needed
            # The graph will loop through the ReAct cycle until it produces a final response
            result = self.agent_graph.invoke(initial_state)

            # Extract final response from messages
            output = ""
            if isinstance(result, dict) and "messages" in result:
                messages = result["messages"]
                if messages:
                    # Get the last message which should be the final response
                    # This will be an AIMessage or similar after the agent finishes
                    last_message = messages[-1]
                    output = str(last_message.content)
            else:
                output = str(result)

            return {"output": output}

    return AgentWrapper(agent)


if __name__ == "__main__":
    # Example usage
    agent = create_lc_agent()
    result = agent.invoke({"input": "What are my main skills?"})
    print(result)
