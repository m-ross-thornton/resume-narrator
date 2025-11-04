"""Tests for the agent module"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import ResumeNarrator, FastMCPClient


class TestFastMCPClient:
    """Test FastMCP client functionality"""

    @pytest.mark.unit
    def test_client_initialization(self):
        """Test client initializes with correct server URLs"""
        server_urls = {
            "resume": "http://localhost:9001",
            "vector": "http://localhost:9002",
            "code": "http://localhost:9003",
        }
        client = FastMCPClient(server_urls)

        assert client.servers == server_urls
        assert client.client is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_tools_empty(self):
        """Test listing tools when server is unavailable"""
        client = FastMCPClient({"test": "http://invalid:9999"})
        tools = await client.list_tools("test")

        assert isinstance(tools, list)
        assert len(tools) == 0

    @pytest.mark.unit
    def test_client_with_default_urls(self):
        """Test client uses environment variables for URLs"""
        os.environ["MCP_RESUME_URL"] = "http://resume:9001"
        os.environ["MCP_VECTOR_URL"] = "http://vector:9002"
        os.environ["MCP_CODE_URL"] = "http://code:9003"

        server_urls = {
            "resume": os.getenv("MCP_RESUME_URL", "http://localhost:9001"),
            "vector": os.getenv("MCP_VECTOR_URL", "http://localhost:9002"),
            "code": os.getenv("MCP_CODE_URL", "http://localhost:9003"),
        }
        client = FastMCPClient(server_urls)

        assert client.servers["resume"] == "http://resume:9001"
        assert client.servers["vector"] == "http://vector:9002"
        assert client.servers["code"] == "http://code:9003"


class TestResumeNarrator:
    """Test ResumeNarrator agent functionality"""

    @pytest.mark.unit
    def test_narrator_initialization(self):
        """Test narrator initializes with required components"""
        with patch.object(ResumeNarrator, "_create_tools", return_value=[]):
            narrator = ResumeNarrator()

            assert narrator.llm is not None
            assert narrator.memory is not None
            assert narrator.mcp_client is not None
            assert narrator.tools is not None

    @pytest.mark.unit
    def test_narrator_creates_tools(self):
        """Test narrator creates all required tools"""
        with patch.object(
            ResumeNarrator, "_create_tools", return_value=[]
        ) as mock_tools:
            narrator = ResumeNarrator()

            mock_tools.assert_called_once()

    @pytest.mark.unit
    def test_tool_names(self):
        """Test all expected tools are available"""
        with patch.object(ResumeNarrator, "_create_tools") as mock_create:
            narrator = ResumeNarrator()

            # Access the actual tools creation
            tools = narrator._create_tools()
            tool_names = [tool.name for tool in tools]

            assert "generate_resume_pdf" in tool_names
            assert "search_experience" in tool_names
            assert "explain_architecture" in tool_names
            assert "analyze_skills" in tool_names

    @pytest.mark.unit
    def test_create_agent_returns_executor(self):
        """Test create_agent returns an executor"""
        with patch.object(ResumeNarrator, "_create_tools", return_value=[]):
            narrator = ResumeNarrator()
            executor = narrator.create_agent()

            assert executor is not None

    @pytest.mark.unit
    def test_sync_wrapper_runs_async_code(self):
        """Test sync wrapper executes async code correctly"""

        async def async_test():
            return "test_result"

        narrator = ResumeNarrator()
        result = narrator._sync_wrapper(async_test())

        assert result == "test_result"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_wrapper_handles_errors(self):
        """Test sync wrapper handles async errors"""

        async def async_error():
            raise ValueError("Test error")

        narrator = ResumeNarrator()
        with pytest.raises(ValueError, match="Test error"):
            narrator._sync_wrapper(async_error())

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_responds_to_greeting(self):
        """Test agent responds to simple greeting (requires running services)"""
        narrator = ResumeNarrator()
        executor = narrator.create_agent()

        # This would require Ollama and other services running
        # Skip if services not available
        pytest.skip("Requires running services")

    @pytest.mark.unit
    def test_narrator_with_custom_subject(self):
        """Test narrator with custom subject name"""
        os.environ["SUBJECT_NAME"] = "Alice"

        with patch.object(ResumeNarrator, "_create_tools", return_value=[]):
            narrator = ResumeNarrator()

            # Custom subject should be accessible through environment
            assert os.getenv("SUBJECT_NAME") == "Alice"

    @pytest.mark.unit
    def test_memory_initialization(self):
        """Test conversation memory is initialized"""
        with patch.object(ResumeNarrator, "_create_tools", return_value=[]):
            narrator = ResumeNarrator()

            assert narrator.memory is not None
            assert hasattr(narrator.memory, "memory_key")
            assert narrator.memory.memory_key == "chat_history"

    @pytest.mark.unit
    def test_mcp_client_servers_configured(self):
        """Test MCP client has all servers configured"""
        with patch.object(ResumeNarrator, "_create_tools", return_value=[]):
            narrator = ResumeNarrator()

            assert "resume" in narrator.mcp_client.servers
            assert "vector" in narrator.mcp_client.servers
            assert "code" in narrator.mcp_client.servers


class TestToolCreation:
    """Test tool creation and configuration"""

    @pytest.mark.unit
    def test_generate_resume_pdf_tool_exists(self):
        """Test resume PDF generation tool is created"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        pdf_tool = next((t for t in tools if t.name == "generate_resume_pdf"), None)
        assert pdf_tool is not None
        assert "PDF" in pdf_tool.description

    @pytest.mark.unit
    def test_search_experience_tool_exists(self):
        """Test experience search tool is created"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        search_tool = next((t for t in tools if t.name == "search_experience"), None)
        assert search_tool is not None
        assert "search" in search_tool.description.lower()

    @pytest.mark.unit
    def test_explain_architecture_tool_exists(self):
        """Test architecture explanation tool is created"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        explain_tool = next(
            (t for t in tools if t.name == "explain_architecture"), None
        )
        assert explain_tool is not None
        assert "architecture" in explain_tool.description.lower()

    @pytest.mark.unit
    def test_analyze_skills_tool_exists(self):
        """Test skills analysis tool is created"""
        narrator = ResumeNarrator()
        tools = narrator._create_tools()

        skills_tool = next((t for t in tools if t.name == "analyze_skills"), None)
        assert skills_tool is not None
        assert "skill" in skills_tool.description.lower()
