# agent/main.py
import httpx
import json
from typing import Dict, Any, List
import os


def _import_langchain():
    """Lazy import langchain to avoid compatibility issues on Python 3.12"""
    from langchain_community.llms import Ollama
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import PromptTemplate
    from langchain.tools import Tool

    return (
        Ollama,
        AgentExecutor,
        create_react_agent,
        ConversationBufferMemory,
        PromptTemplate,
        Tool,
    )


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
        # Lazy import to avoid Python 3.12 compatibility issues
        (
            Ollama,
            AgentExecutor,
            create_react_agent,
            ConversationBufferMemory,
            PromptTemplate,
            Tool,
        ) = _import_langchain()

        self.llm = Ollama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )

        self.memory = ConversationBufferMemory()

        # Initialize MCP client
        self.mcp_client = FastMCPClient(
            {
                "resume": os.getenv("MCP_RESUME_URL", "http://localhost:9001"),
                "vector": os.getenv("MCP_VECTOR_URL", "http://localhost:9002"),
                "code": os.getenv("MCP_CODE_URL", "http://localhost:9003"),
            }
        )

        self.tools = self._create_tools()

    def _create_tools(self) -> List:
        """Create LangChain tools from MCP servers"""
        _, _, _, _, _, Tool = _import_langchain()
        tools = []

        # Resume PDF Generation Tool
        tools.append(
            Tool(
                name="generate_resume_pdf",
                description="Generate a professional PDF resume. Input should be a JSON string with template and sections.",
                func=lambda x: self._sync_wrapper(
                    self.mcp_client.call_tool(
                        "resume", "generate_resume_pdf", json.loads(x)
                    )
                ),
            )
        )

        # Vector Search Tool
        tools.append(
            Tool(
                name="search_experience",
                description="Search through professional experience and projects. Input should be a search query string.",
                func=lambda x: self._sync_wrapper(
                    self.mcp_client.call_tool(
                        "vector", "search_experience", {"query": x}
                    )
                ),
            )
        )

        # Architecture Explanation Tool
        tools.append(
            Tool(
                name="explain_architecture",
                description="Explain the architecture of how the chatbot works. Input should be component name (agent, mcp_servers, deployment, or full_stack).",
                func=lambda x: self._sync_wrapper(
                    self.mcp_client.call_tool(
                        "code", "explain_architecture", {"component": x}
                    )
                ),
            )
        )

        # Skill Analysis Tool
        tools.append(
            Tool(
                name="analyze_skills",
                description="Analyze skill coverage across experiences. No input needed.",
                func=lambda x: self._sync_wrapper(
                    self.mcp_client.call_tool("vector", "analyze_skill_coverage", {})
                ),
            )
        )

        return tools

    def _sync_wrapper(self, coro):
        """Wrapper to run async functions in sync context"""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def create_agent(self):
        """Create the LangChain agent"""
        (
            Ollama,
            AgentExecutor,
            create_react_agent,
            ConversationBufferMemory,
            PromptTemplate,
            Tool,
        ) = _import_langchain()

        prompt = PromptTemplate(
            input_variables=[
                "tools",
                "tool_names",
                "agent_scratchpad",
                "input",
            ],
            template="""You are a helpful AI assistant that can use the following tools to answer questions and complete tasks.

You have access to these tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT:
- Always follow the format strictly
- Action must be one of the tool names listed
- Always use "Final Answer:" when you have completed the task
- Do not output anything else

Begin!

Question: {input}
Thought:{agent_scratchpad}""",
        )

        # Create the agent
        agent = create_react_agent(self.llm, self.tools, prompt)

        # Create the agent executor with custom error handling
        def handle_parsing_errors(error):
            """Custom error handler for parsing errors"""
            error_msg = str(error)
            if "Final Answer:" in error_msg or "final answer" in error_msg.lower():
                # If the model tried to give a final answer but format was wrong,
                # extract it anyway
                return f"Final Answer: {error_msg}"
            return f"I encountered an issue processing that request. Error: {error_msg[:100]}"

        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=handle_parsing_errors,
        )

        return agent_executor
