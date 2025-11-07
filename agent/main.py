# agent/main.py
import json
from typing import Dict, Any, List
import os
import sys
from pathlib import Path


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


def _import_mcp_servers():
    """Import MCP server modules directly"""
    # Add mcp-servers directory to path
    mcp_servers_dir = Path(__file__).parent.parent / "mcp-servers"
    if str(mcp_servers_dir) not in sys.path:
        sys.path.insert(0, str(mcp_servers_dir))

    try:
        # Import server modules
        import resume_pdf_server
        import vector_db_server
        import code_explorer_server

        return {
            "resume": resume_pdf_server,
            "vector": vector_db_server,
            "code": code_explorer_server,
        }
    except ImportError as e:
        print(f"Warning: Could not import MCP servers: {e}")
        return {}


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

        # Import MCP servers directly
        self.mcp_servers = _import_mcp_servers()

        self.tools = self._create_tools()

    def _create_tools(self) -> List:
        """Create LangChain tools from MCP servers"""
        _, _, _, _, _, Tool = _import_langchain()
        tools = []

        # Resume PDF Generation Tool
        def generate_resume_pdf(input_str):
            try:
                if self.mcp_servers and "resume" in self.mcp_servers:
                    resume_module = self.mcp_servers["resume"]
                    params = (
                        json.loads(input_str)
                        if isinstance(input_str, str)
                        else input_str
                    )
                    # Call the generate_resume function from the server
                    result = resume_module.generate_resume(params)
                    return str(result)
                return "Resume server not available"
            except Exception as e:
                return f"Error generating resume: {str(e)}"

        tools.append(
            Tool(
                name="generate_resume_pdf",
                description="Generate a professional PDF resume. Input should be a JSON string with template and sections.",
                func=generate_resume_pdf,
            )
        )

        # Vector Search Tool
        def search_experience(query):
            try:
                if self.mcp_servers and "vector" in self.mcp_servers:
                    vector_module = self.mcp_servers["vector"]
                    # Call the search function from the server
                    result = vector_module.search_vectors(query)
                    return str(result)
                return "Vector search server not available"
            except Exception as e:
                return f"Error searching experience: {str(e)}"

        tools.append(
            Tool(
                name="search_experience",
                description="Search through professional experience and projects. Input should be a search query string.",
                func=search_experience,
            )
        )

        # Architecture Explanation Tool
        def explain_architecture(component):
            try:
                if self.mcp_servers and "code" in self.mcp_servers:
                    code_module = self.mcp_servers["code"]
                    # Call the explain function from the server
                    result = code_module.explain_component(component)
                    return str(result)
                return "Code explorer server not available"
            except Exception as e:
                return f"Error explaining architecture: {str(e)}"

        tools.append(
            Tool(
                name="explain_architecture",
                description="Explain the architecture of how the chatbot works. Input should be component name (agent, mcp_servers, deployment, or full_stack).",
                func=explain_architecture,
            )
        )

        # Skill Analysis Tool
        def analyze_skills(input_str):
            try:
                if self.mcp_servers and "vector" in self.mcp_servers:
                    vector_module = self.mcp_servers["vector"]
                    # Call the analyze function from the server
                    result = vector_module.analyze_skills()
                    return str(result)
                return "Vector search server not available"
            except Exception as e:
                return f"Error analyzing skills: {str(e)}"

        tools.append(
            Tool(
                name="analyze_skills",
                description="Analyze skill coverage across experiences. No input needed.",
                func=analyze_skills,
            )
        )

        return tools

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

Begin!

Question: {input}
Thought:{agent_scratchpad}""",
        )

        # Create the agent
        agent = create_react_agent(self.llm, self.tools, prompt)

        # Create the agent executor
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=self.tools, verbose=True, max_iterations=10
        )

        return agent_executor
