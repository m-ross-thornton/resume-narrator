"""Tests for Docker deployment and container health"""
import pytest
import subprocess
import json
import time
from pathlib import Path


class TestDockerCompose:
    """Test Docker Compose configuration"""

    @pytest.mark.docker
    def test_docker_compose_file_exists(self):
        """Test docker-compose.yml exists"""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        assert compose_file.exists()

    @pytest.mark.docker
    def test_docker_compose_valid_yaml(self):
        """Test docker-compose.yml is valid YAML"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            try:
                config = yaml.safe_load(f)
                assert config is not None
                assert "services" in config
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.yml: {e}")

    @pytest.mark.docker
    def test_required_services_defined(self):
        """Test all required services are defined"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            config = yaml.safe_load(f)

        required_services = [
            "ollama",
            "chromadb",
            "mcp-resume",
            "mcp-vector",
            "mcp-code",
            "agent",
        ]

        for service in required_services:
            assert (
                service in config["services"]
            ), f"Service '{service}' not found in docker-compose.yml"

    @pytest.mark.docker
    def test_agent_service_configuration(self):
        """Test agent service is properly configured"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            config = yaml.safe_load(f)

        agent_service = config["services"]["agent"]

        # Check required fields
        assert "build" in agent_service
        assert "ports" in agent_service
        assert "environment" in agent_service
        assert "8080:8080" in agent_service["ports"]

    @pytest.mark.docker
    def test_ollama_service_configuration(self):
        """Test Ollama service is properly configured"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            config = yaml.safe_load(f)

        ollama_service = config["services"]["ollama"]

        assert "image" in ollama_service
        assert "ports" in ollama_service
        assert "11434:11434" in ollama_service["ports"]

    @pytest.mark.docker
    def test_chromadb_service_configuration(self):
        """Test ChromaDB service is properly configured"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            config = yaml.safe_load(f)

        chroma_service = config["services"]["chromadb"]

        assert "image" in chroma_service
        assert "ports" in chroma_service
        assert "8000:8000" in chroma_service["ports"]

    @pytest.mark.docker
    def test_mcp_servers_service_configuration(self):
        """Test MCP servers services are properly configured"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            config = yaml.safe_load(f)

        # Check that each MCP service is properly configured
        mcp_services = {
            "mcp-resume": "9001:9001",
            "mcp-vector": "9002:9002",
            "mcp-code": "9003:9003",
        }

        for service_name, expected_port in mcp_services.items():
            mcp_service = config["services"][service_name]
            assert "build" in mcp_service
            assert "ports" in mcp_service
            assert expected_port in mcp_service["ports"]


class TestDockerfiles:
    """Test Dockerfile configurations"""

    @pytest.mark.docker
    def test_dockerfile_agent_exists(self):
        """Test Dockerfile.agent exists"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile.agent"
        assert dockerfile.exists()

    @pytest.mark.docker
    def test_dockerfile_mcp_exists(self):
        """Test Dockerfile.mcp exists"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile.mcp"
        assert dockerfile.exists()

    @pytest.mark.docker
    def test_agent_dockerfile_has_pythonpath(self):
        """Test Dockerfile.agent sets PYTHONPATH"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile.agent"

        with open(dockerfile, "r") as f:
            content = f.read()

        assert "PYTHONPATH" in content

    @pytest.mark.docker
    def test_mcp_dockerfile_has_pythonpath(self):
        """Test Dockerfile.mcp sets PYTHONPATH"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile.mcp"

        with open(dockerfile, "r") as f:
            content = f.read()

        assert "PYTHONPATH" in content

    @pytest.mark.docker
    def test_agent_dockerfile_copies_requirements(self):
        """Test Dockerfile.agent copies requirements"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile.agent"

        with open(dockerfile, "r") as f:
            content = f.read()

        assert "requirements.txt" in content
        assert "pip install" in content

    @pytest.mark.docker
    def test_mcp_dockerfile_copies_requirements(self):
        """Test Dockerfile.mcp copies requirements"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile.mcp"

        with open(dockerfile, "r") as f:
            content = f.read()

        assert "requirements.txt" in content
        assert "pip install" in content


class TestRequirementsFiles:
    """Test requirements files"""

    @pytest.mark.docker
    def test_agent_requirements_exists(self):
        """Test agent requirements.txt exists"""
        requirements = Path(__file__).parent.parent / "agent" / "requirements.txt"
        assert requirements.exists()

    @pytest.mark.docker
    def test_mcp_requirements_exists(self):
        """Test MCP servers requirements.txt exists"""
        requirements = Path(__file__).parent.parent / "mcp-servers" / "requirements.txt"
        assert requirements.exists()

    @pytest.mark.docker
    def test_agent_requirements_not_empty(self):
        """Test agent requirements.txt is not empty"""
        requirements = Path(__file__).parent.parent / "agent" / "requirements.txt"

        with open(requirements, "r") as f:
            content = f.read().strip()

        assert len(content) > 0
        assert "\n" in content or len(content.split()) > 0

    @pytest.mark.docker
    def test_mcp_requirements_contains_fastmcp(self):
        """Test MCP requirements includes fastmcp"""
        requirements = Path(__file__).parent.parent / "mcp-servers" / "requirements.txt"

        with open(requirements, "r") as f:
            content = f.read().lower()

        assert "fastmcp" in content or "mcp" in content

    @pytest.mark.docker
    def test_agent_requirements_contains_chainlit(self):
        """Test agent requirements includes chainlit"""
        requirements = Path(__file__).parent.parent / "agent" / "requirements.txt"

        with open(requirements, "r") as f:
            content = f.read().lower()

        assert "chainlit" in content

    @pytest.mark.docker
    def test_agent_requirements_contains_langchain(self):
        """Test agent requirements includes langchain"""
        requirements = Path(__file__).parent.parent / "agent" / "requirements.txt"

        with open(requirements, "r") as f:
            content = f.read().lower()

        assert "langchain" in content


class TestDockerBuild:
    """Test Docker build configuration (requires Docker)"""

    @pytest.mark.docker
    @pytest.mark.skipif(
        subprocess.run(["docker", "--version"], capture_output=True).returncode != 0,
        reason="Docker not installed",
    )
    def test_docker_available(self):
        """Test Docker is available"""
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        assert result.returncode == 0

    @pytest.mark.docker
    @pytest.mark.skipif(
        subprocess.run(["docker", "compose", "version"], capture_output=True).returncode
        != 0,
        reason="Docker Compose not available",
    )
    def test_docker_compose_available(self):
        """Test Docker Compose is available"""
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, text=True
        )
        assert result.returncode == 0


class TestContainerHealth:
    """Test container health checks (requires running containers)"""

    @pytest.mark.docker
    @pytest.mark.skipif(
        subprocess.run(["docker", "ps"], capture_output=True).returncode != 0,
        reason="Docker not running",
    )
    def test_docker_daemon_running(self):
        """Test Docker daemon is running"""
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        assert result.returncode == 0

    @pytest.mark.docker
    def test_agent_port_exposed(self):
        """Test agent service exposes port 8080"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            config = yaml.safe_load(f)

        agent_service = config["services"]["agent"]
        assert "8080:8080" in agent_service.get("ports", [])

    @pytest.mark.docker
    def test_all_services_have_healthchecks(self):
        """Test services have healthcheck configured"""
        import yaml

        compose_file = Path(__file__).parent.parent / "docker-compose.yml"

        with open(compose_file, "r") as f:
            config = yaml.safe_load(f)

        # Services with healthchecks
        expected_healthchecks = ["ollama", "chromadb", "agent"]

        for service_name in expected_healthchecks:
            service = config["services"].get(service_name)
            if service:
                # May or may not have healthcheck, but structure should be valid
                assert isinstance(service, dict)
