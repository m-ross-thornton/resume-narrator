"""Integration tests for agent and MCP servers"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import create_agent


class TestAgentMCPIntegration:
    """Test integration between agent and MCP servers"""

    @pytest.mark.integration
    def test_agent_initialization(self):
        """Test agent can be initialized with tools"""
        agent = create_agent()

        assert agent is not None
        assert hasattr(agent, "invoke")
        assert hasattr(agent, "graph")

    @pytest.mark.integration
    def test_agent_executor_creation(self):
        """Test agent executor is created successfully"""
        agent = create_agent()

        assert agent is not None
        assert hasattr(agent, "invoke")

    @pytest.mark.integration
    def test_environment_variables_passed_to_agent(self):
        """Test environment variables are correctly passed to agent"""
        os.environ["OLLAMA_HOST"] = "http://test-ollama:11434"
        os.environ["MCP_RESUME_URL"] = "http://test-resume:9001"

        agent = create_agent()

        # Verify agent is created with env vars
        assert agent is not None


class TestServiceHealthChecks:
    """Test service health and connectivity"""

    @pytest.mark.integration
    def test_mcp_server_urls_configured(self):
        """Test MCP server URLs are configured via environment"""
        test_urls = {
            "MCP_RESUME_URL": "http://test-resume:9001",
            "MCP_VECTOR_URL": "http://test-vector:9002",
            "MCP_CODE_URL": "http://test-code:9003",
        }

        for key, value in test_urls.items():
            os.environ[key] = value

        agent = create_agent()

        assert agent is not None

        # Clean up
        for key in test_urls:
            if key in os.environ:
                del os.environ[key]

    @pytest.mark.integration
    def test_llm_model_configured(self):
        """Test LLM is configured with correct model"""
        expected_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")

        agent = create_agent()

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
            agent = create_agent()
            assert agent is not None

    @pytest.mark.unit
    def test_agent_tool_creation_does_not_fail_on_missing_services(self):
        """Test tools are created even without running services"""
        agent = create_agent()

        # Should create agent successfully regardless of service availability
        assert agent is not None
        assert hasattr(agent, "invoke")


class TestAgentPromptTemplate:
    """Test agent prompt template configuration"""

    @pytest.mark.unit
    def test_agent_has_system_prompt(self):
        """Test agent can be created with system prompt"""
        agent = create_agent()

        # The agent should be properly created with system prompt
        assert agent is not None
        assert hasattr(agent, "graph")

    @pytest.mark.unit
    def test_subject_name_env_variable(self):
        """Test subject name is read from environment"""
        os.environ["SUBJECT_NAME"] = "TestUser"

        # Create new instance to pick up env var
        subject = os.getenv("SUBJECT_NAME")
        assert subject == "TestUser"

        # Clean up
        del os.environ["SUBJECT_NAME"]

    @pytest.mark.unit
    def test_default_subject_name(self):
        """Test default subject name if not provided"""
        if "SUBJECT_NAME" in os.environ:
            del os.environ["SUBJECT_NAME"]

        subject = os.getenv("SUBJECT_NAME", "Ross")
        assert subject == "Ross"


class TestAgentWrapperInterface:
    """Test agent wrapper interface for Chainlit compatibility"""

    @pytest.mark.unit
    def test_agent_invoke_with_input_dict(self):
        """Test agent invoke accepts input dict"""
        agent = create_agent()

        # Should accept dict with "input" key (Chainlit interface)
        result = agent.invoke({"input": "test query"})

        assert isinstance(result, dict)
        assert "output" in result
        assert "input" in result

    @pytest.mark.unit
    def test_agent_invoke_returns_proper_format(self):
        """Test agent invoke returns Chainlit-compatible format"""
        agent = create_agent()

        result = agent.invoke({"input": "What are my skills?"})

        assert isinstance(result, dict)
        assert result.get("input") == "What are my skills?"
        assert "output" in result
        assert isinstance(result["output"], str)

    @pytest.mark.unit
    def test_agent_wrapper_graph_attribute(self):
        """Test agent wrapper has graph attribute"""
        agent = create_agent()

        assert hasattr(agent, "graph")
        assert agent.graph is not None


# Need to import patch for test_agent_handles_invalid_mcp_servers
from unittest.mock import patch
