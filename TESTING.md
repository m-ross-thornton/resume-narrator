# Testing Guide

This document describes the testing requirements and procedures for the Resnar project.

## Overview

The Resnar project includes comprehensive unit, integration, and Docker deployment tests. All tests must pass before committing to GitHub.

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_agent.py               # Agent (ResumeNarrator) tests
├── test_mcp_servers.py         # MCP server tests
├── test_mcp_integration.py     # Integration tests
├── test_chainlit_app.py        # Chainlit UI tests
└── test_docker_deployment.py   # Docker deployment tests
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual components in isolation
- Fast execution (no external services required)
- Can be run without Docker
- Examples: Class initialization, method behavior, data validation

### Integration Tests (`@pytest.mark.integration`)
- Test interaction between components
- May require running services (Ollama, ChromaDB, MCP servers)
- Test end-to-end workflows
- Examples: Agent with MCP servers, Chainlit with agent

### Docker Tests (`@pytest.mark.docker`)
- Test Docker configuration and deployment
- Validate docker-compose.yml, Dockerfiles
- Verify requirements files
- No external dependencies

### Async Tests (`@pytest.mark.asyncio`)
- Test async/await functionality
- Used with async tests
- Automatically handled by pytest-asyncio

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio pyyaml
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Category

```bash
# Unit tests only
pytest tests/ -m unit

# Integration tests only
pytest tests/ -m integration

# Docker tests only
pytest tests/ -m docker

# Skip integration tests (faster)
pytest tests/ -m "not integration"
```

### Run Specific Test File

```bash
pytest tests/test_agent.py
pytest tests/test_mcp_servers.py
pytest tests/test_mcp_integration.py
pytest tests/test_chainlit_app.py
pytest tests/test_docker_deployment.py
```

### Run Specific Test

```bash
pytest tests/test_agent.py::TestResumeNarrator::test_narrator_initialization
```

### Verbose Output

```bash
pytest tests/ -v
```

### Show Print Statements

```bash
pytest tests/ -s
```

## Test Requirements by Category

### Unit Tests (No Services Required)
- Pytest
- Python 3.11+
- Project dependencies (chainlit, langchain, etc.)

### Integration Tests (Requires Running Services)
- All unit test requirements
- Docker and Docker Compose
- Running services: `docker-compose up -d`
- Services must be healthy

### Docker Tests (No Services Required)
- Pytest
- PyYAML (for docker-compose.yml validation)
- Docker CLI (optional, for docker build tests)

## Before Committing to GitHub

Run this checklist:

```bash
# 1. Run all unit tests
pytest tests/ -m unit -v

# 2. Check code formatting with Black
black --check agent/ mcp-servers/ tests/

# 3. Run pre-commit hooks (includes Black + Docker tests)
pre-commit run --all-files

# 4. Docker validation is now part of pre-commit!
# (pytest tests/test_docker_deployment.py runs automatically)

# 5. Optional: Run integration tests (requires running services)
docker-compose up -d
pytest tests/ -m integration -v
docker-compose down
```

## Pre-Commit Hooks

Pre-commit is now configured to run:
- **Black**: Code formatting check
- **pytest-docker**: Docker configuration tests

These will run automatically before each commit via `.pre-commit-config.yaml`.

## Test Coverage

Expected test coverage:
- Agent module: ~85%
- MCP servers: ~75%
- Chainlit app: ~70%
- Docker configuration: ~90%

Generate coverage report:
```bash
pytest tests/ --cov=agent --cov=mcp-servers --cov-report=html
```

## Debugging Tests

### Debug a Single Test

```bash
pytest tests/test_agent.py::TestResumeNarrator::test_narrator_initialization -vv -s
```

### Use PDB Debugger

```bash
pytest tests/test_agent.py::TestResumeNarrator::test_narrator_initialization --pdb
```

### Stop on First Failure

```bash
pytest tests/ -x
```

## Test Examples

### Unit Test Example

```python
@pytest.mark.unit
def test_narrator_initialization():
    """Test narrator initializes with required components"""
    narrator = ResumeNarrator()

    assert narrator.llm is not None
    assert narrator.memory is not None
    assert narrator.mcp_client is not None
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent can be initialized with MCP servers"""
    narrator = ResumeNarrator()

    assert narrator.llm is not None
    assert narrator.mcp_client is not None
```

### Docker Test Example

```python
@pytest.mark.docker
def test_docker_compose_file_exists():
    """Test docker-compose.yml exists"""
    compose_file = Path("docker-compose.yml")
    assert compose_file.exists()
```

## Fixtures

Available fixtures (from conftest.py):

- `test_data_path`: Path to test data directory
- `mock_resume_data`: Sample resume data
- `mock_experience_documents`: Sample experience documents

Usage:
```python
def test_with_fixture(mock_resume_data):
    assert mock_resume_data["contact"]["name"] == "Ross"
```

## Continuous Integration

Tests are configured to run automatically on:
- Pre-commit (via pre-commit hooks)
- Pull requests (via GitHub Actions)
- Manual execution before deployment

## Common Issues and Solutions

### Issue: "ModuleNotFoundError: No module named 'agent'"
**Solution**: Run pytest from project root: `cd /Users/ross/Projects/resnar && pytest`

### Issue: "Services unavailable" in integration tests
**Solution**: Start services: `docker-compose up -d` before running integration tests

### Issue: "Permission denied" for Docker tests
**Solution**: Add your user to docker group: `sudo usermod -aG docker $USER`

### Issue: Async tests not running
**Solution**: Ensure pytest-asyncio is installed: `pip install pytest-asyncio`

## Adding New Tests

1. Create test file in `tests/` directory
2. Name it `test_*.py`
3. Use appropriate markers (@pytest.mark.unit, @pytest.mark.integration, etc.)
4. Add docstrings explaining what is being tested
5. Run tests locally before committing
6. Update TESTING.md if adding new test categories

## Test Statistics

Current test count:
- Unit tests: ~60
- Integration tests: ~20
- Docker tests: ~25
- Total: ~105 tests

Expected execution time:
- Unit tests only: ~5-10 seconds
- All tests (with services): ~30-60 seconds
- Docker tests only: ~2-3 seconds

## Troubleshooting

### Tests hang or timeout
- Check if Docker services are running properly
- Verify network connectivity to services
- Increase pytest timeout: `pytest --timeout=300`

### Tests fail intermittently
- May indicate race conditions or timing issues
- Run tests multiple times: `pytest tests/ --count=5`
- Check service health: `docker-compose ps`

### Specific test fails locally but passes in CI
- Check Python version matches (should be 3.11+)
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check environment variables are set correctly

## Support

For issues or questions about testing:
1. Check this guide (TESTING.md)
2. Review test source code
3. Run tests with verbose output (-vv)
4. Check pytest documentation: https://pytest.org/
