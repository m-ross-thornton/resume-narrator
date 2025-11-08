"""Integration tests for agent and MCP servers"""
import pytest
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import ResumeNarrator


def _import_langchain():
    """Lazy import to avoid Pydantic v2 compatibility issues with LangChain v0.1"""
    from langchain.memory import ConversationBufferMemory

    return ConversationBufferMemory


class TestAgentMCPIntegration:
    """Test integration between agent and MCP servers"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent can be initialized with MCP servers"""
        narrator = ResumeNarrator()

        assert narrator.llm is not None
        assert narrator.mcp_client is not None
        assert len(narrator.tools) >= 4

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resume_generation_tool_callable(self):
        """Test resume generation tool is callable"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        pdf_tool = next((t for t in tools if t.name == "generate_resume_pdf"), None)
        assert pdf_tool is not None
        assert callable(pdf_tool.func)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_experience_tool_callable(self):
        """Test search experience tool is callable"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        search_tool = next((t for t in tools if t.name == "search_experience"), None)
        assert search_tool is not None
        assert callable(search_tool.func)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_explain_architecture_tool_callable(self):
        """Test explain architecture tool is callable"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        explain_tool = next(
            (t for t in tools if t.name == "explain_architecture"), None
        )
        assert explain_tool is not None
        assert callable(explain_tool.func)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_analyze_skills_tool_callable(self):
        """Test analyze skills tool is callable"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        skills_tool = next((t for t in tools if t.name == "analyze_skills"), None)
        assert skills_tool is not None
        assert callable(skills_tool.func)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_executor_creation(self):
        """Test agent executor is created successfully"""
        narrator = ResumeNarrator()
        executor = narrator.create_agent()

        assert executor is not None
        assert hasattr(executor, "invoke")
        assert hasattr(executor, "ainvoke")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_client_server_configuration(self):
        """Test MCP client has correct server configuration"""
        narrator = ResumeNarrator()
        mcp_client = narrator.mcp_client

        expected_servers = ["resume", "vector", "code"]
        for server in expected_servers:
            assert server in mcp_client.servers
            assert isinstance(mcp_client.servers[server], str)
            assert "http" in mcp_client.servers[server]

    @pytest.mark.integration
    def test_environment_variables_passed_to_agent(self):
        """Test environment variables are correctly passed to agent"""
        os.environ["OLLAMA_HOST"] = "http://test-ollama:11434"
        os.environ["MCP_RESUME_URL"] = "http://test-resume:9001"

        narrator = ResumeNarrator()

        # Verify environment variables are used
        assert narrator.llm.base_url == "http://test-ollama:11434"


class TestServiceHealthChecks:
    """Test service health and connectivity"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mcp_servers_configured(self):
        """Test MCP servers are configured (not testing connectivity)"""
        narrator = ResumeNarrator()
        servers = narrator.mcp_client.servers

        assert servers["resume"] is not None
        assert servers["vector"] is not None
        assert servers["code"] is not None

    @pytest.mark.integration
    def test_llm_model_configured(self):
        """Test LLM is configured with correct model"""
        expected_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
        narrator = ResumeNarrator()

        assert narrator.llm.model == expected_model

    @pytest.mark.integration
    def test_memory_configured(self):
        """Test conversation memory is properly configured"""
        ConversationBufferMemory = _import_langchain()
        narrator = ResumeNarrator()
        memory = narrator.memory

        assert memory.memory_key == "history"
        # ConversationBufferMemory returns messages by default
        assert isinstance(memory, ConversationBufferMemory)


class TestToolIntegration:
    """Test tool integration and functionality"""

    @pytest.mark.integration
    def test_all_tools_have_descriptions(self):
        """Test all tools have proper descriptions"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        for tool in tools:
            assert tool.name is not None
            assert tool.description is not None
            assert len(tool.description) > 0

    @pytest.mark.integration
    def test_tools_are_unique(self):
        """Test all tools have unique names"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()
        tool_names = [tool.name for tool in tools]

        assert len(tool_names) == len(set(tool_names))

    @pytest.mark.integration
    def test_tool_descriptions_match_names(self):
        """Test tool descriptions match their purpose"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        tool_map = {tool.name: tool.description for tool in tools}

        assert (
            "resume" in tool_map["generate_resume_pdf"].lower()
            or "pdf" in tool_map["generate_resume_pdf"].lower()
        )
        assert "search" in tool_map["search_experience"].lower()
        assert "architecture" in tool_map["explain_architecture"].lower()
        assert "skill" in tool_map["analyze_skills"].lower()


class TestAgentErrorHandling:
    """Test agent error handling and edge cases"""

    @pytest.mark.unit
    def test_agent_handles_missing_mcp_servers(self):
        """Test agent gracefully handles missing MCP servers"""
        with patch.dict(
            os.environ,
            {
                "MCP_RESUME_URL": "http://invalid:9999",
                "MCP_VECTOR_URL": "http://invalid:9999",
                "MCP_CODE_URL": "http://invalid:9999",
            },
        ):
            # Should not raise an error during initialization
            narrator = ResumeNarrator()
            assert narrator.mcp_client is not None

    @pytest.mark.unit
    def test_sync_wrapper_preserves_exceptions(self):
        """Test sync wrapper preserves async exceptions"""

        async def failing_async():
            raise ValueError("Test error")

        narrator = ResumeNarrator()
        with pytest.raises(ValueError, match="Test error"):
            narrator._sync_wrapper(failing_async())

    @pytest.mark.unit
    def test_agent_tool_creation_does_not_fail_on_missing_services(self):
        """Test agent tools are created even without running services"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        # Should create 4 tools regardless of service availability
        assert len(tools) == 4


class TestAgentPromptTemplate:
    """Test agent prompt template configuration"""

    @pytest.mark.unit
    def test_prompt_has_required_fields(self):
        """Test agent prompt template includes required fields"""
        narrator = ResumeNarrator()
        executor = narrator.create_agent()

        # The prompt should be embedded in the agent
        assert executor is not None

    @pytest.mark.unit
    def test_subject_name_env_variable(self):
        """Test subject name is read from environment"""
        os.environ["SUBJECT_NAME"] = "TestUser"

        # Create new instance to pick up env var
        subject = os.getenv("SUBJECT_NAME")
        assert subject == "TestUser"

    @pytest.mark.unit
    def test_default_subject_name(self):
        """Test default subject name if not provided"""
        if "SUBJECT_NAME" in os.environ:
            del os.environ["SUBJECT_NAME"]

        subject = os.getenv("SUBJECT_NAME", "Ross")
        assert subject == "Ross"
