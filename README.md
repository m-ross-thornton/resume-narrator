# Resnar - Resume Narrator AI

A comprehensive AI agent system for generating, analyzing, and explaining professional resumes using LLMs, vector databases, and modular microservices.

## Overview

Resnar is a sophisticated resume narrator application that combines:
- **LLM-powered Agent**: Uses LangChain with Ollama for intelligent interactions
- **MCP Servers**: Modular server architecture for specialized tasks
- **Vector Database**: ChromaDB for semantic search across experience
- **Web UI**: Chainlit-based interactive interface
- **Docker Deployment**: Complete containerized stack for easy deployment

## Features

### 🤖 Agent Capabilities
- **Resume Generation**: Create professional PDF resumes with customizable templates
- **Experience Search**: Semantic search through professional experience and projects
- **Architecture Explanation**: Understand how the system works internally
- **Skill Analysis**: Analyze and report on skill coverage across experiences

### 🔧 MCP Servers
- **Resume PDF Server**: Generate PDFs with multiple templates (professional, creative, technical, executive)
- **Vector DB Server**: Semantic search and document indexing with ChromaDB
- **Code Explorer Server**: Analyze and explain codebase architecture

### 🎨 User Interface
- **Chainlit Web UI**: Interactive chat interface at `http://localhost:8080`
- **Real-time Response Streaming**: Immediate feedback from LLM queries
- **Session Management**: Maintain conversation context

## Quick Start

### Prerequisites
- Docker (with Compose plugin)
- Python 3.11+ (for local development)
- Ollama (or use Docker version)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/resnar.git
cd resnar

# Start all services
docker compose up -d

# Check service status
docker compose ps

# Access the UI
open http://localhost:8080
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r agent/requirements.txt
pip install -r test-requirements.txt

# Start services manually
docker compose up -d ollama chromadb mcp-servers

# Run the Chainlit app
chainlit run agent/ui/chainlit_app.py --host 0.0.0.0 --port 8080
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Agent (Chainlit) | 8080 | Web UI for interacting with the agent |
| Ollama | 11434 | LLM inference server |
| ChromaDB | 8000 | Vector database for semantic search |
| MCP Servers | 9001-9003 | Microservices (Resume, Vector DB, Code) |
| Prometheus | 9090 | Metrics collection (optional) |
| Grafana | 3000 | Metrics visualization (optional) |

## Architecture

```
┌─────────────────────────────────────────────┐
│         Chainlit Web UI (8080)              │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│      ResumeNarrator Agent                   │
│  (LangChain + Ollama LLM)                   │
└────┬──────────┬──────────┬──────────────────┘
     │          │          │
┌────▼──┐  ┌───▼──┐  ┌────▼──┐
│Resume │  │Vector│  │Code   │
│Server │  │DB    │  │Server │
│(9001) │  │(9002)│  │(9003) │
└────┬──┘  └───┬──┘  └────┬──┘
     │         │         │
     └────┬────┴────┬────┘
          │         │
       ┌──▼──┐  ┌──▼──┐
       │Ollama│  │Chroma│
       │(11434)  │DB    │
       └──────┘  └──────┘
```

## Configuration

### Environment Variables

Create a `.env` file (see `.env.example`):

```env
# Ollama
OLLAMA_HOST=http://ollama:11434

# ChromaDB
CHROMA_HOST=http://chromadb:8000

# MCP Servers
MCP_RESUME_URL=http://mcp-servers:9001
MCP_VECTOR_URL=http://mcp-servers:9002
MCP_CODE_URL=http://mcp-servers:9003

# Agent
SUBJECT_NAME=Ross
```

### Docker Compose Configuration

See `docker-compose.yml` for detailed service configuration (used with `docker compose` command) including:
- Health checks for each service
- Volume mounts for data persistence
- Network configuration
- Resource limits

## Testing

Comprehensive test suite with 105+ tests covering unit, integration, and deployment scenarios.

### Quick Test

```bash
# Install test dependencies
pip install -r test-requirements.txt

# Run unit tests
./run_tests.sh unit

# Run Docker configuration tests
./run_tests.sh docker

# Run all tests
./run_tests.sh all
```

### Pre-Commit Hooks

Pre-commit is configured to automatically run:
- **Black**: Code formatting
- **pytest-docker**: Docker configuration validation

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

See [TESTING.md](TESTING.md) for comprehensive testing guide.

## Development

### Project Structure

```
resnar/
├── agent/                    # Main agent module
│   ├── ui/                  # Chainlit web UI
│   ├── chains/              # LangChain chains
│   ├── main.py              # ResumeNarrator implementation
│   └── requirements.txt      # Agent dependencies
├── mcp-servers/             # MCP microservices
│   ├── resume_pdf_server.py
│   ├── vector_db_server.py
│   ├── code_explorer_server.py
│   └── requirements.txt
├── tests/                    # Comprehensive test suite
│   ├── conftest.py
│   ├── test_agent.py
│   ├── test_mcp_servers.py
│   ├── test_mcp_integration.py
│   ├── test_chainlit_app.py
│   └── test_docker_deployment.py
├── data/                     # Data directory (mounted in containers)
├── monitoring/               # Prometheus/Grafana config
├── docker-compose.yml        # Service orchestration
├── Dockerfile.agent          # Agent container
├── Dockerfile.mcp            # MCP servers container
├── pytest.ini                # Pytest configuration
├── .pre-commit-config.yaml   # Pre-commit hooks
├── TESTING.md                # Testing guide
├── COMMIT_CHECKLIST.md       # Pre-commit checklist
└── README.md                 # This file
```

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/resnar.git
cd resnar

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r agent/requirements.txt
pip install -r test-requirements.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
./run_tests.sh unit
```

### Making Changes

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `./run_tests.sh unit`
4. Format code: `black agent/ mcp-servers/ tests/`
5. Commit: `git add . && git commit -m "feat: your change"`
6. Push: `git push origin feature/your-feature`
7. Create Pull Request

## Deployment

### Using Docker Compose

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f agent

# Stop services
docker compose down

# Remove volumes
docker compose down -v
```

### Health Checks

All services include health checks. Monitor them with:

```bash
docker compose ps
```

Test individual services:

```bash
# Ollama
curl http://localhost:11434/api/tags

# ChromaDB
curl http://localhost:8000/api/v2/heartbeat

# Agent
curl http://localhost:8080
```

## API

### Chainlit Endpoints

- `GET /` - Web UI
- `WebSocket /ws` - Real-time chat
- `GET /health` - Health check

### MCP Server Endpoints

Resume Server (9001):
- `POST /tool/generate_resume_pdf` - Generate resume PDF

Vector DB Server (9002):
- `POST /tool/search_experience` - Search experience
- `POST /tool/analyze_skill_coverage` - Analyze skills

Code Server (9003):
- `POST /tool/explain_architecture` - Explain architecture

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Run full test suite: `./run_tests.sh all`
6. Ensure pre-commit passes: `pre-commit run --all-files`
7. Submit a pull request

See [COMMIT_CHECKLIST.md](COMMIT_CHECKLIST.md) for detailed pre-commit requirements.

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or use different port in docker-compose.yml
```

### Service Health Issues

```bash
# Check service logs
docker-compose logs agent
docker-compose logs ollama
docker-compose logs chromadb

# Restart a service
docker-compose restart agent

# Full reset
docker-compose down -v
docker-compose up -d
```

### Dependencies Issues

```bash
# Update Python dependencies
pip install --upgrade -r agent/requirements.txt

# Check for conflicts
pip check

# Rebuild Docker images
docker-compose build --no-cache
```

See [TESTING.md](TESTING.md) for more troubleshooting tips.

## Documentation

- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [COMMIT_CHECKLIST.md](COMMIT_CHECKLIST.md) - Pre-commit requirements
- [TESTS_SUMMARY.md](TESTS_SUMMARY.md) - Test suite overview

## License

[Your License Here]

## Author

Ross - Created 2024

## Support

For issues, questions, or suggestions:
1. Check existing issues on GitHub
2. Review [TESTING.md](TESTING.md) and [COMMIT_CHECKLIST.md](COMMIT_CHECKLIST.md)
3. Create a new issue with detailed description

## Roadmap

- [ ] Additional LLM model support
- [ ] Advanced prompt engineering
- [ ] User authentication
- [ ] Multi-user sessions
- [ ] Custom templates
- [ ] Export to multiple formats
- [ ] Advanced analytics
- [ ] API rate limiting
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline

## Acknowledgments

- LangChain - LLM orchestration
- Chainlit - Web UI framework
- Ollama - Local LLM inference
- ChromaDB - Vector database
- FastMCP - Microservice framework
