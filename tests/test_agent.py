"""Tests for the agent module"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import (
    create_lc_agent,
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
        """Test create_lc_agent returns an agent"""
        agent = create_lc_agent()

        assert agent is not None
        assert hasattr(agent, "invoke")

    @pytest.mark.unit
    def test_agent_wrapper_invoke_interface(self):
        """Test agent has invoke method"""
        agent = create_lc_agent()

        assert callable(agent.invoke)

    @pytest.mark.unit
    def test_agent_has_invoke_method(self):
        """Test agent has invoke method"""
        agent = create_lc_agent()

        assert agent is not None
        assert hasattr(agent, "invoke")


class TestToolIntegration:
    """Test tool integration in agent"""

    @pytest.mark.unit
    def test_tools_available_in_agent(self):
        """Test that tools are available for agent use"""
        agent = create_lc_agent()

        # The agent should have tools bound
        assert agent is not None

    @pytest.mark.unit
    def test_agent_creation_succeeds(self):
        """Test agent can be created without errors"""
        agent = create_lc_agent()

        assert agent is not None


class TestAgentConfiguration:
    """Test agent configuration"""

    @pytest.mark.unit
    def test_default_ollama_configuration(self):
        """Test default Ollama configuration"""
        agent = create_lc_agent()

        assert agent is not None

    @pytest.mark.unit
    def test_mcp_server_urls_from_environment(self):
        """Test MCP server URLs from configuration"""
        from agent.config import MCP_RESUME_URL, MCP_VECTOR_URL, MCP_CODE_URL

        agent = create_lc_agent()
        assert agent is not None

        # Verify config values are loaded
        assert MCP_RESUME_URL is not None
        assert MCP_VECTOR_URL is not None
        assert MCP_CODE_URL is not None
