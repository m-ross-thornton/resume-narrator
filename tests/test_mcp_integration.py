"""Integration tests for agent and MCP servers"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import create_lc_agent


class TestAgentMCPIntegration:
    """Test integration between agent and MCP servers"""

    @pytest.mark.integration
    def test_agent_with_custom_mcp_server_urls(self):
        """Test agent initialization with custom MCP server URLs"""
        # Set custom server URLs
        os.environ["MCP_RESUME_URL"] = "http://custom-resume:9001"
        os.environ["MCP_VECTOR_URL"] = "http://custom-vector:9002"
        os.environ["MCP_CODE_URL"] = "http://custom-code:9003"

        try:
            agent = create_lc_agent()
            assert agent is not None
            assert hasattr(agent, "invoke")
        finally:
            # Clean up
            del os.environ["MCP_RESUME_URL"]
            del os.environ["MCP_VECTOR_URL"]
            del os.environ["MCP_CODE_URL"]


class TestServiceHealthChecks:
    """Test service health and connectivity"""

    @pytest.mark.integration
    def test_agent_can_handle_mcp_server_urls(self):
        """Test agent can work with different MCP server configurations"""
        from agent.config import MCP_RESUME_URL, MCP_VECTOR_URL, MCP_CODE_URL

        # Verify the config module can read URLs (from environment or defaults)
        assert MCP_RESUME_URL is not None
        assert MCP_VECTOR_URL is not None
        assert MCP_CODE_URL is not None

        # Agent should be created regardless of server availability
        agent = create_lc_agent()
        assert agent is not None


class TestAgentErrorHandling:
    """Test agent error handling and edge cases"""

    @pytest.mark.unit
    def test_agent_handles_invalid_mcp_servers(self):
        """Test agent gracefully handles invalid MCP server URLs"""
        with patch.dict(
            os.environ,
            {
                "MCP_RESUME_URL": "http://invalid:9999",
                "MCP_VECTOR_URL": "http://invalid:9999",
                "MCP_CODE_URL": "http://invalid:9999",
            },
        ):
            # Should not raise an error during initialization
            agent = create_lc_agent()
            assert agent is not None

    @pytest.mark.unit
    def test_agent_tool_creation_does_not_fail_on_missing_services(self):
        """Test tools are created even without running services"""
        agent = create_lc_agent()

        # Should create agent successfully regardless of service availability
        assert agent is not None
        assert hasattr(agent, "invoke")


class TestAgentPromptTemplate:
    """Test agent prompt template and initialization"""

    @pytest.mark.unit
    def test_agent_initializes_successfully(self):
        """Test agent can be created and is ready for use"""
        agent = create_lc_agent()

        # The agent should be properly created and invokable
        assert agent is not None
        assert hasattr(agent, "invoke")


class TestAgentWrapperInterface:
    """Test agent interface - Note: invoke method tests are in test_agent.py"""

    @pytest.mark.unit
    def test_agent_is_langchain_runnable(self):
        """Test agent is a proper LangChain Runnable with invoke capability"""
        agent = create_lc_agent()

        # ChatOllama with bind_tools is a LangChain Runnable
        assert agent is not None
        assert callable(agent.invoke)
        # Can be used with LangChain's async/stream utilities
        assert hasattr(agent, "invoke")


# Need to import patch for test_agent_handles_invalid_mcp_servers
from unittest.mock import patch
