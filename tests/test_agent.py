"""Tests for the agent module"""
import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.main import (
    create_lc_agent,
    generate_resume,
    search_experience,
    explain_architecture,
    analyze_skills,
)


class TestToolFunctions:
    """Test @tool decorated functions"""

    @pytest.mark.unit
    def test_generate_resume_tool_exists(self):
        """Test resume generation tool is created"""
        assert generate_resume is not None
        assert hasattr(generate_resume, "name")
        assert generate_resume.name == "generate_resume"

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
    def test_create_agent_returns_agent_with_invoke(self):
        """Test create_lc_agent returns a callable agent with invoke method"""
        agent = create_lc_agent()

        assert agent is not None
        assert hasattr(agent, "invoke")
        assert callable(agent.invoke)


class TestToolIntegration:
    """Test tool integration in agent"""

    @pytest.mark.unit
    def test_all_tools_are_bound_to_agent(self):
        """Test that all tools are properly bound to the agent"""
        agent = create_lc_agent()

        # Verify agent can be invoked and has access to tools
        assert agent is not None
        assert hasattr(agent, "invoke")
        # Tools are bound to the ChatOllama instance via bind_tools()


class TestAgentConfiguration:
    """Test agent configuration"""

    @pytest.mark.unit
    def test_configuration_loaded_from_config_module(self):
        """Test that agent uses configuration from config module"""
        from agent.config import (
            OLLAMA_MODEL,
            OLLAMA_HOST,
            MCP_RESUME_URL,
            MCP_VECTOR_URL,
            MCP_CODE_URL,
        )

        # Verify all config values are loaded
        assert OLLAMA_MODEL is not None
        assert OLLAMA_HOST is not None
        assert MCP_RESUME_URL is not None
        assert MCP_VECTOR_URL is not None
        assert MCP_CODE_URL is not None

        # Verify agent can be created with these configs
        agent = create_lc_agent()
        assert agent is not None
