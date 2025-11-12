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


class CustomReActAgent:
    """Custom ReAct agent that properly handles tool invocation."""

    def __init__(self, llm: ChatOllama, tools: List[Any]):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = 10

    def invoke(self, input_dict: dict) -> dict:
        """Invoke agent with user input and return response."""
        user_input = input_dict.get("input", "")

        # Initialize message history
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_input),
        ]

        logger.info(f"Starting agent with input: {user_input[:100]}")

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            logger.debug(f"Iteration {iteration}")

            # Get LLM response
            response = self.llm.invoke(messages)
            logger.debug(
                f"LLM response type: {type(response).__name__}, "
                f"content preview: {str(response.content)[:200]}"
            )

            # Add LLM response to messages
            messages.append(response)

            # Try to parse tool calls from response
            tool_calls = self._parse_tool_calls(response.content)

            if not tool_calls:
                # No tool calls, return final response
                logger.info(f"No tool calls detected, returning response")
                return {"output": str(response.content)}

            # Execute tool calls
            logger.debug(f"Found {len(tool_calls)} tool calls")
            for tool_call in tool_calls:
                tool_result = self._execute_tool(tool_call)
                logger.debug(f"Tool {tool_call['name']} result: {tool_result[:200]}")

                # Add tool result to messages
                messages.append(
                    ToolMessage(
                        content=tool_result, tool_call_id=tool_call.get("id", "")
                    )
                )

        logger.warning(f"Reached max iterations ({self.max_iterations})")
        return {
            "output": "I reached the maximum number of iterations without a final answer."
        }

    def _parse_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response."""
        tool_calls = []

        # Pattern 1: JSON-formatted tool calls
        # {"name": "search_experience", "parameters": {...}}
        json_pattern = (
            r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"parameters"\s*:\s*(\{[^}]+\})\s*\}'
        )
        for match in re.finditer(json_pattern, content):
            tool_name = match.group(1)
            params_str = match.group(2)
            try:
                params = json.loads(params_str)
                if tool_name in self.tools:
                    tool_calls.append(
                        {
                            "id": f"call_{len(tool_calls)}",
                            "name": tool_name,
                            "args": params,
                        }
                    )
                    logger.debug(f"Parsed tool call: {tool_name} with params {params}")
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON params: {e}")

        # Pattern 2: Function call syntax
        # search_experience(query="...") or search_experience(query='...')
        func_pattern = r"(\w+)\s*\(\s*([^)]*)\s*\)"
        for match in re.finditer(func_pattern, content):
            tool_name = match.group(1)
            args_str = match.group(2)

            if tool_name in self.tools and not any(
                tc["name"] == tool_name for tc in tool_calls
            ):
                try:
                    # Try to parse as kwargs
                    args_dict = {}
                    for arg in args_str.split(","):
                        if "=" in arg:
                            key, val = arg.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("'\"")
                            args_dict[key] = val

                    if args_dict or tool_name in ["analyze_skills"]:
                        tool_calls.append(
                            {
                                "id": f"call_{len(tool_calls)}",
                                "name": tool_name,
                                "args": args_dict if args_dict else {},
                            }
                        )
                        logger.debug(
                            f"Parsed function call: {tool_name} with args {args_dict}"
                        )
                except Exception as e:
                    logger.debug(f"Failed to parse function call {tool_name}: {e}")

        return tool_calls

    def _execute_tool(self, tool_call: Dict[str, Any]) -> str:
        """Execute a single tool call."""
        tool_name = tool_call["name"]
        args = tool_call.get("args", {})

        logger.info(f"Executing tool: {tool_name} with args: {args}")

        if tool_name not in self.tools:
            error_msg = f"Tool {tool_name} not found"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

        try:
            tool = self.tools[tool_name]
            # Call the tool with the provided arguments
            result = tool.func(**args)
            logger.debug(f"Tool {tool_name} returned: {result[:200]}")
            return result
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})


def create_lc_agent() -> Any:
    """Create the Resume Narrator agent with proper tool invocation.

    Returns an agent that accepts {"input": "..."} and returns {"output": "..."}.
    The agent automatically executes tools in a loop until it has a final answer.
    """
    # Initialize LLM with configured settings
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0.3,
        num_ctx=4096,  # Context window
        num_predict=2048,  # Max tokens for response
    )

    # Define tools
    tools = [
        generate_resume_pdf,
        search_experience,
        explain_architecture,
        analyze_skills,
    ]

    # Create custom ReAct agent that properly handles tool invocation
    agent = CustomReActAgent(llm, tools)

    # Wrapper to match Chainlit expectations
    class AgentWrapper:
        def __init__(self, custom_agent):
            self.agent = custom_agent

        def invoke(self, input_dict: dict) -> dict:
            """Invoke agent and return response."""
            try:
                return self.agent.invoke(input_dict)
            except Exception as e:
                logger.error(f"Error invoking agent: {e}", exc_info=True)
                return {
                    "output": f"I encountered an error while processing your request: {str(e)}"
                }

    return AgentWrapper(agent)


if __name__ == "__main__":
    # Example usage
    agent = create_lc_agent()
    result = agent.invoke({"input": "What are my main skills?"})
    print(result)
