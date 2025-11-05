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
            model="llama3.2:latest",
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
                description="Explain how the chatbot works. Input should be component name (agent, mcp_servers, deployment, or full_stack).",
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
        _, AgentExecutor, create_react_agent, _, PromptTemplate, _ = _import_langchain()
        prompt = PromptTemplate(
            input_variables=["tools", "tool_names", "chat_history"],
            template="""You are a personal AI assistant with specialized capabilities:

1. **Resume Generation**: Create professional PDF resumes with various templates
2. **Experience Search**: Search through a database of professional experiences and projects
3. **Self-Documentation**: Explain your own architecture and how you work
4. **Skill Analysis**: Analyze and report on skill coverage

Available tools:
{tools}

Tool Names: {tool_names}

When using tools, ensure you format the input correctly:
- For generate_resume_pdf: Use JSON format with "template" and "sections" keys
- For search_experience: Provide a search query string
- For explain_architecture: Specify component (agent, mcp_servers, deployment, or full_stack)
- For analyze_skills: No input needed

Chat History:
{chat_history}
""",
        )
