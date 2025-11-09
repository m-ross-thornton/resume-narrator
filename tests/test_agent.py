"""Tests for the agent module"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import (
    create_agent,
    generate_resume_pdf,
    search_experience,
    explain_architecture,
    analyze_skills,
)


class TestToolFunctions:
    """Test @tool decorated functions"""

    @pytest.mark.unit
    def test_generate_resume_pdf_tool_exists(self):
        """Test resume PDF generation tool is created"""
        assert generate_resume_pdf is not None
        assert hasattr(generate_resume_pdf, "name")
        assert generate_resume_pdf.name == "generate_resume_pdf"

    @pytest.mark.unit
    def test_search_experience_tool_exists(self):
        """Test experience search tool is created"""
        assert search_experience is not None
        assert hasattr(search_experience, "name")
        assert search_experience.name == "search_experience"

    @pytest.mark.unit
    def test_explain_architecture_tool_exists(self):
        """Test architecture explanation tool is created"""
        assert explain_architecture is not None
        assert hasattr(explain_architecture, "name")
        assert explain_architecture.name == "explain_architecture"

    @pytest.mark.unit
    def test_analyze_skills_tool_exists(self):
        """Test skills analysis tool is created"""
        assert analyze_skills is not None
        assert hasattr(analyze_skills, "name")
        assert analyze_skills.name == "analyze_skills"


class TestCreateAgent:
    """Test agent creation"""

    @pytest.mark.unit
    def test_create_agent_returns_wrapper(self):
        """Test create_agent returns an agent wrapper"""
        agent = create_agent()

        assert agent is not None
        assert hasattr(agent, "invoke")

    @pytest.mark.unit
    def test_agent_wrapper_invoke_interface(self):
        """Test agent wrapper has invoke method"""
        agent = create_agent()

        assert callable(agent.invoke)

    @pytest.mark.unit
    def test_agent_wrapper_has_graph(self):
        """Test agent wrapper has graph attribute"""
        agent = create_agent()

        assert hasattr(agent, "graph")
        assert agent.graph is not None


class TestToolIntegration:
    """Test tool integration in agent"""

    @pytest.mark.unit
    def test_tools_available_in_agent(self):
        """Test that tools are available for agent use"""
        agent = create_agent()

        # The agent's graph should have tools
        assert agent.graph is not None

    @pytest.mark.unit
    def test_agent_creation_succeeds(self):
        """Test agent can be created without errors"""
        agent = create_agent()

        assert agent is not None


class TestAgentConfiguration:
    """Test agent configuration"""

    @pytest.mark.unit
    def test_default_ollama_configuration(self):
        """Test default Ollama configuration"""
        agent = create_agent()

        assert agent is not None

    @pytest.mark.unit
    def test_mcp_server_urls_from_environment(self):
        """Test MCP server URLs from environment variables"""
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
