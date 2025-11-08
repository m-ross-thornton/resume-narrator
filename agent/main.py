"""
Resume Narrator Agent using LangChain 1.0 and langgraph
"""
import httpx
import json
from typing import Dict, Any, List, TypedDict, Annotated
import os
import operator
import asyncio


class AgentState(TypedDict):
    """State for the agent graph"""

    messages: Annotated[List, operator.add]
    input: str
    output: str


class FastMCPClient:
    """Client to interact with FastMCP servers"""

    def __init__(self, server_urls: Dict[str, str]):
        self.servers = server_urls
        self.client = httpx.AsyncClient(timeout=30.0)

    async def call_tool(self, server: str, tool: str, params: Dict) -> Dict:
        """Call a tool on an MCP server"""
        url = f"{self.servers[server]}/tool/{tool}"

        try:
            response = await self.client.post(url, json=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to call tool: {str(e)}"}

    async def list_tools(self, server: str) -> List[Dict]:
        """List available tools from a server"""
        url = f"{self.servers[server]}/tools"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []


class ResumeNarrator:
    def __init__(self):
        from langchain_community.llms import Ollama
        from langchain_core.tools import StructuredTool
        from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

        self.llm = Ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

        # Initialize MCP client
        self.mcp_client = FastMCPClient(
            {
                "resume": os.getenv("MCP_RESUME_URL", "http://localhost:9001"),
                "vector": os.getenv("MCP_VECTOR_URL", "http://localhost:9002"),
                "code": os.getenv("MCP_CODE_URL", "http://localhost:9003"),
            }
        )

        self.tools = self._create_tools()
        self.StructuredTool = StructuredTool
        self.HumanMessage = HumanMessage
        self.AIMessage = AIMessage

    def _create_tools(self) -> List:
        """Create LangChain tools from MCP servers"""
        from langchain_core.tools import StructuredTool

        tools = []

        # Resume PDF Generation Tool
        tools.append(
            StructuredTool.from_function(
                func=self._generate_resume_pdf,
                name="generate_resume_pdf",
                description="Generate a professional PDF resume. Input should be template type and sections to include.",
            )
        )

        # Vector Search Tool
        tools.append(
            StructuredTool.from_function(
                func=self._search_experience,
                name="search_experience",
                description="Search through professional experience and projects. Input should be a search query string.",
            )
        )

        # Architecture Explanation Tool
        tools.append(
            StructuredTool.from_function(
                func=self._explain_architecture,
                name="explain_architecture",
                description="Explain the architecture of how the chatbot works. Input should be component name (agent, mcp_servers, deployment, or full_stack).",
            )
        )

        # Skill Analysis Tool
        tools.append(
            StructuredTool.from_function(
                func=self._analyze_skills,
                name="analyze_skills",
                description="Analyze skill coverage across experiences. No input needed.",
            )
        )

        return tools

    def _generate_resume_pdf(
        self, template: str = "professional", sections: str = ""
    ) -> str:
        """Generate resume PDF"""
        try:
            params = {
                "template": template,
                "sections": sections.split(",") if sections else [],
            }
            result = self._sync_wrapper(
                self.mcp_client.call_tool("resume", "generate_resume_pdf", params)
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _search_experience(self, query: str) -> str:
        """Search experience"""
        try:
            result = self._sync_wrapper(
                self.mcp_client.call_tool(
                    "vector", "search_experience", {"query": query}
                )
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _explain_architecture(self, component: str = "full_stack") -> str:
        """Explain architecture"""
        try:
            result = self._sync_wrapper(
                self.mcp_client.call_tool(
                    "code", "explain_architecture", {"component": component}
                )
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _analyze_skills(self) -> str:
        """Analyze skills"""
        try:
            result = self._sync_wrapper(
                self.mcp_client.call_tool("vector", "analyze_skill_coverage", {})
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _sync_wrapper(self, coro):
        """Wrapper to run async functions in sync context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def create_agent(self):
        """Create the LangChain 1.0 agent using langgraph"""
        from langchain_core.messages import (
            BaseMessage,
            HumanMessage,
            AIMessage,
            ToolMessage,
        )
        from langchain_core.tools import StructuredTool
        from langgraph.graph import StateGraph, END

        # Create a mapping of tool names to functions for execution
        tool_map = {tool.name: tool for tool in self.tools}

        # Define the agent node - decides whether to use tools or return final answer
        def agent_node(state: AgentState) -> AgentState:
            """Agent node that decides which tool to use or provides final answer"""
            messages = state.get("messages", [])
            input_text = state.get("input", "")

            # If no messages, create initial message
            if not messages:
                messages = [HumanMessage(content=input_text)]

            # Call LLM with tools
            llm_with_tools = self.llm.bind_tools(self.tools)
            response = llm_with_tools.invoke(messages)

            # Add response to messages
            new_messages = messages + [response]

            return {
                "messages": new_messages,
                "input": input_text,
                "output": getattr(response, "content", str(response)),
            }

        # Define the tool execution node
        def tool_node(state: AgentState) -> AgentState:
            """Execute tools based on agent decision"""
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None

            # Get tool calls from last message
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_calls = last_message.tool_calls
            else:
                return state

            # Execute tools and collect results
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                tool_input = tool_call.get("args", {})
                tool_id = tool_call.get("id", "")

                # Execute the tool
                if tool_name in tool_map:
                    try:
                        result = tool_map[tool_name].invoke(tool_input)
                    except Exception as e:
                        result = f"Error executing {tool_name}: {str(e)}"
                else:
                    result = f"Tool {tool_name} not found"

                tool_results.append(
                    ToolMessage(
                        content=result
                        if isinstance(result, str)
                        else json.dumps(result),
                        tool_call_id=tool_id,
                    )
                )

            new_messages = messages + tool_results
            return {
                "messages": new_messages,
                "input": state.get("input", ""),
                "output": state.get("output", ""),
            }

        # Define routing logic
        def should_continue(state: AgentState) -> str:
            """Decide whether to continue with tools or end"""
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None

            # If last message has tool calls, continue to tool execution
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            # Otherwise end
            return "end"

        # Build the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)

        # Add edges
        workflow.add_edge("tools", "agent")
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END,
            },
        )

        # Set entry point
        workflow.set_entry_point("agent")

        # Compile
        return workflow.compile()
