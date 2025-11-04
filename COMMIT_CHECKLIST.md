# Commit Checklist for GitHub

Before committing any changes to GitHub, ensure all items in this checklist are completed.

## ✅ Pre-Commit Requirements

### Code Quality

- [ ] **Code Formatting**
  ```bash
  black agent/ mcp-servers/ tests/
  ```
  - All Python code follows Black code style
  - Run Black to auto-format if needed

- [ ] **Pre-commit Hooks**
  ```bash
  pre-commit run --all-files
  ```
  - Pre-commit hooks pass (Black + Docker tests)
  - Install if not already: `pip install pre-commit`
  - Includes: Black code formatting + Docker configuration tests
  - Configured in `.pre-commit-config.yaml`

### Testing

- [ ] **Unit Tests Pass**
  ```bash
  pytest tests/ -m unit -v
  ```
  - All unit tests pass
  - No test errors or failures
  - Expected: ~60 unit tests

- [ ] **Docker Configuration Tests Pass**
  ```bash
  pytest tests/test_docker_deployment.py -v
  ```
  - All Docker-related tests pass
  - docker-compose.yml is valid
  - Dockerfiles are properly configured

- [ ] **Code Imports Verified**
  ```bash
  pytest tests/test_mcp_servers.py -v
  pytest tests/test_chainlit_app.py -v
  ```
  - All modules can be imported without errors
  - No missing dependencies

### Optional: Integration Tests (Requires Services)

- [ ] **Services Running** (if testing integration)
  ```bash
  docker compose up -d
  docker compose ps  # All containers should be healthy
  ```

- [ ] **Integration Tests Pass** (if testing with services)
  ```bash
  pytest tests/ -m integration -v
  ```
  - Agent initialization works
  - Tools are properly configured
  - MCP servers are accessible

- [ ] **Services Healthy**
  - Ollama: `curl http://localhost:11434/api/tags`
  - ChromaDB: `curl http://localhost:8000/api/v2/heartbeat`
  - Agent: `curl http://localhost:8080`

- [ ] **Stop Services After Testing**
  ```bash
  docker compose down
  ```

### Documentation

- [ ] **README.md Updated** (if applicable)
  - New features documented
  - Setup instructions updated
  - Known issues listed

- [ ] **Code Comments Added**
  - Complex logic explained
  - API endpoints documented
  - Configuration options noted

- [ ] **TESTING.md Reviewed**
  - Test instructions are current
  - Test categories are accurate
  - Examples are correct

### Files to Review

- [ ] **Dockerfile.agent**
  - Uses correct base image
  - All dependencies installed
  - PYTHONPATH correctly set
  - Port 8080 exposed

- [ ] **Dockerfile.mcp**
  - Uses correct base image
  - FastMCP installed
  - Server runner configured
  - PYTHONPATH correctly set

- [ ] **docker-compose.yml**
  - All services defined
  - Ports correctly exposed
  - Environment variables set
  - Volumes mounted properly
  - Healthchecks configured

- [ ] **requirements.txt Files**
  - Agent requirements valid
  - MCP server requirements valid
  - No conflicting versions
  - All dependencies specified

### Git

- [ ] **No Uncommitted Changes**
  ```bash
  git status
  ```
  - Clean working directory
  - All changes staged for commit

- [ ] **Commit Message Format**
  - Clear description of changes
  - References any related issues
  - Follows conventional commits (optional)
  - Example: "feat: add Docker compose configuration"

- [ ] **Branch is Up to Date**
  ```bash
  git pull origin main
  ```
  - No merge conflicts
  - Branch is ahead of origin

## 📋 Full Test Command

Run this complete test sequence before commit:

```bash
#!/bin/bash

echo "Running full test sequence..."

# 1. Format code
echo "Formatting code with Black..."
black agent/ mcp-servers/ tests/

# 2. Run pre-commit hooks
echo "Running pre-commit hooks..."
pre-commit run --all-files

# 3. Run unit tests
echo "Running unit tests..."
pytest tests/ -m unit -v

# 4. Check git status
echo "Checking git status..."
git status

echo "✓ All checks complete!"
```

Or simply run:
```bash
./run_tests.sh unit
```

**Note**: Pre-commit now includes Docker tests automatically via the `pytest-docker` hook configured in `.pre-commit-config.yaml`, so separate Docker testing is no longer needed.

## 🐳 Docker Deployment Checklist

Before deployment to production:

- [ ] **Container Images Built**
  ```bash
  docker compose build
  ```

- [ ] **All Services Start Successfully**
  ```bash
  docker compose up -d
  sleep 30  # Allow services to initialize
  docker compose ps
  ```

- [ ] **All Services Healthy**
  ```bash
  docker compose ps
  # All containers should show "Up" status
  ```

- [ ] **Agent UI Accessible**
  ```bash
  curl http://localhost:8080
  # Should return HTML
  ```

- [ ] **No Error Logs**
  ```bash
  docker-compose logs --tail=50
  # No ERROR or CRITICAL messages
  ```

- [ ] **Services Respond to Requests**
  - Ollama: `curl http://localhost:11434/api/tags`
  - ChromaDB: `curl http://localhost:8000/api/v2/heartbeat`
  - Agent: `curl http://localhost:8080`

## 📊 Test Coverage Goals

- **Agent Module**: ≥ 80% coverage
- **MCP Servers**: ≥ 70% coverage
- **Chainlit App**: ≥ 65% coverage
- **Docker Config**: ≥ 85% coverage

Generate coverage report:
```bash
pytest tests/ --cov=agent --cov=mcp-servers --cov-report=html
open htmlcov/index.html
```

## 🚀 Final Steps Before Push

```bash
# 1. Ensure all tests pass
./run_tests.sh unit

# 2. Format code
black agent/ mcp-servers/ tests/

# 3. Add all changes
git add .

# 4. Create commit with descriptive message
git commit -m "feat: add Docker compose and comprehensive tests"

# 5. Review what will be pushed
git log origin/main..HEAD

# 6. Push to GitHub
git push origin your-branch-name
```

## ❌ Common Issues and Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'agent'` | Run pytest from project root |
| `Services unavailable` | Start Docker services: `docker compose up -d` |
| `Black formatting issues` | Run `black agent/ mcp-servers/ tests/` |
| `Import errors in tests` | Ensure PYTHONPATH is set correctly |
| `Port already in use` | Check `lsof -i :8080` and kill process or use different port |

## 📝 Notes

- All tests should pass locally before pushing
- Integration tests are optional for commit but recommended
- Always review docker-compose.yml for port conflicts (uses `docker compose` command)
- Ensure PYTHONPATH is set in all Dockerfiles
- Document any new test categories added

---

**Last Updated**: 2024-11-04
**Status**: Ready for initial commit
