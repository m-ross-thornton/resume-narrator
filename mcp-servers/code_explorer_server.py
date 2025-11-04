# mcp_servers/code_explorer_server.py
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import ast
import os
from pathlib import Path
import subprocess
import yaml
import json

mcp = FastMCP("code-explorer-server")


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis"""

    component: str = Field(
        ...,
        description="Component to analyze: agent, mcp_servers, deployment, or full_stack",
    )
    detail_level: str = Field(
        default="overview",
        description="Level of detail: overview, detailed, or code_examples",
    )
    specific_file: Optional[str] = Field(
        default=None, description="Specific file to analyze"
    )


class ArchitectureExplorer:
    """Explore and explain the chatbot architecture"""

    def __init__(self, codebase_root: str = "/app/codebase"):
        self.codebase_root = Path(codebase_root)
        self.architecture_map = self._build_architecture_map()

    def _build_architecture_map(self) -> Dict:
        """Build a map of the codebase architecture"""
        return {
            "agent": {
                "path": self.codebase_root / "agent",
                "description": "Core agent implementation using LangChain and Chainlit",
                "key_files": {
                    "main.py": "Main agent initialization and configuration",
                    "ui/chainlit_app.py": "Chainlit UI implementation",
                    "chains/": "Custom LangChain chains for specific tasks",
                },
                "technologies": ["LangChain", "Chainlit", "Ollama"],
                "responsibilities": [
                    "LLM orchestration",
                    "Tool management",
                    "User interface",
                    "Conversation memory",
                ],
            },
            "mcp_servers": {
                "path": self.codebase_root / "mcp_servers",
                "description": "FastMCP tool servers providing specialized capabilities",
                "key_files": {
                    "resume_pdf_server.py": "Resume generation tools",
                    "vector_db_server.py": "Vector search and indexing tools",
                    "code_explorer_server.py": "Self-documentation tools",
                },
                "technologies": ["FastMCP", "ChromaDB", "ReportLab"],
                "responsibilities": [
                    "Tool exposure via MCP protocol",
                    "Specialized functionality",
                    "Data management",
                ],
            },
            "deployment": {
                "path": self.codebase_root,
                "description": "Container orchestration and deployment configuration",
                "key_files": {
                    "docker-compose.yml": "Multi-container orchestration",
                    "Dockerfile.agent": "Agent container configuration",
                    "Dockerfile.mcp": "MCP servers container",
                },
                "technologies": ["Docker", "Docker Compose", "GitHub Actions"],
                "responsibilities": [
                    "Container management",
                    "Service orchestration",
                    "Environment configuration",
                    "CI/CD pipeline",
                ],
            },
            "data": {
                "path": self.codebase_root / "data",
                "description": "Data storage and vector embeddings",
                "structure": {
                    "resume/": "Resume templates and data",
                    "experience/": "Professional experience JSON files",
                    "embeddings/": "ChromaDB vector storage",
                },
            },
        }

    def analyze_python_file(self, filepath: Path) -> Dict:
        """Analyze a Python file for structure and complexity"""
        try:
            with open(filepath, "r") as f:
                content = f.read()

            tree = ast.parse(content)

            analysis = {
                "file": str(filepath),
                "lines_of_code": len(content.splitlines()),
                "classes": [],
                "functions": [],
                "imports": [],
                "decorators": [],
            }

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis["classes"].append(
                        {
                            "name": node.name,
                            "methods": [
                                m.name
                                for m in node.body
                                if isinstance(m, ast.FunctionDef)
                            ],
                            "line_number": node.lineno,
                        }
                    )
                elif isinstance(node, ast.FunctionDef):
                    if node.col_offset == 0:  # Top-level function
                        analysis["functions"].append(
                            {
                                "name": node.name,
                                "args": [arg.arg for arg in node.args.args],
                                "line_number": node.lineno,
                                "is_async": isinstance(node, ast.AsyncFunctionDef),
                            }
                        )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    analysis["imports"].append(f"{node.module}")

            return analysis

        except Exception as e:
            return {"error": f"Failed to analyze file: {str(e)}"}

    def get_docker_compose_info(self) -> Dict:
        """Extract information from docker-compose.yml"""
        try:
            compose_path = self.codebase_root / "docker-compose.yml"
            with open(compose_path, "r") as f:
                compose_data = yaml.safe_load(f)

            services = {}
            for service_name, service_config in compose_data.get(
                "services", {}
            ).items():
                services[service_name] = {
                    "image": service_config.get("image"),
                    "build": service_config.get("build"),
                    "ports": service_config.get("ports", []),
                    "environment": list(service_config.get("environment", {}).keys())
                    if isinstance(service_config.get("environment"), dict)
                    else [],
                    "depends_on": service_config.get("depends_on", []),
                    "volumes": service_config.get("volumes", []),
                }

            return {
                "version": compose_data.get("version"),
                "services": services,
                "networks": list(compose_data.get("networks", {}).keys()),
                "volumes": list(compose_data.get("volumes", {}).keys()),
            }

        except Exception as e:
            return {"error": f"Failed to parse docker-compose.yml: {str(e)}"}


@mcp.tool()
async def explain_architecture(request: CodeAnalysisRequest) -> Dict[str, Any]:
    """
    Explain how the chatbot architecture works

    Args:
        request: Component and detail level to explain

    Returns:
        Detailed explanation of the requested component
    """
    try:
        explorer = ArchitectureExplorer()

        if request.component == "full_stack":
            # Provide complete architecture overview
            explanation = {
                "overview": "This is a modular AI agent system with three main layers:",
                "layers": {
                    "1_presentation": {
                        "component": "Chainlit UI",
                        "responsibility": "User interaction and conversation management",
                        "details": "Provides a web-based chat interface with real-time streaming",
                    },
                    "2_orchestration": {
                        "component": "LangChain Agent",
                        "responsibility": "LLM orchestration and tool routing",
                        "details": "Manages conversation flow, memory, and tool selection",
                    },
                    "3_tools": {
                        "component": "FastMCP Servers",
                        "responsibility": "Specialized functionality via MCP protocol",
                        "details": "Provides resume generation, vector search, and self-documentation",
                    },
                    "4_infrastructure": {
                        "component": "Docker Compose Stack",
                        "responsibility": "Container orchestration and networking",
                        "details": "Manages Ollama, ChromaDB, and all application services",
                    },
                },
                "data_flow": [
                    "User sends message via Chainlit UI",
                    "LangChain agent processes with Ollama LLM",
                    "Agent determines if tools are needed",
                    "FastMCP servers execute tool calls",
                    "Results are formatted and returned to user",
                ],
                "deployment": explorer.get_docker_compose_info(),
            }

            if request.detail_level == "detailed":
                explanation["components"] = explorer.architecture_map

        elif request.component in explorer.architecture_map:
            component_info = explorer.architecture_map[request.component]
            explanation = {
                "component": request.component,
                "description": component_info["description"],
                "technologies": component_info["technologies"],
                "responsibilities": component_info["responsibilities"],
            }

            if request.detail_level in ["detailed", "code_examples"]:
                explanation["key_files"] = component_info["key_files"]

                if request.specific_file:
                    file_path = component_info["path"] / request.specific_file
                    if file_path.exists():
                        explanation["file_analysis"] = explorer.analyze_python_file(
                            file_path
                        )

            if request.detail_level == "code_examples":
                # Add code snippets
                explanation["code_examples"] = await get_code_snippets(
                    request.component
                )

        else:
            return {
                "status": "error",
                "message": f"Unknown component: {request.component}",
                "available_components": list(explorer.architecture_map.keys()),
            }

        return {"status": "success", "explanation": explanation}

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to explain architecture: {str(e)}",
        }


@mcp.tool()
async def get_code_snippets(component: str) -> Dict[str, str]:
    """
    Get relevant code snippets for a component

    Args:
        component: Component to get snippets for

    Returns:
        Dictionary of code snippets
    """
    snippets = {
        "agent": {
            "initialization": """
# Agent initialization example
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor

class PersonalAIAgent:
    def __init__(self):
        self.llm = Ollama(model="llama3.2:latest")
        self.tools = self._load_mcp_tools()
        
    def _load_mcp_tools(self):
        # Connect to FastMCP servers
        return load_tools_from_mcp()
            """,
            "tool_usage": """
# How the agent uses MCP tools
response = await agent.invoke({
    "input": "Generate my resume as a PDF"
})
# Agent automatically routes to resume_pdf_server
            """,
        },
        "mcp_servers": {
            "tool_definition": '''
# FastMCP tool definition
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def my_tool(param: str) -> Dict:
    """Tool description for LLM"""
    return {"result": process(param)}
            ''',
            "server_startup": """
# MCP server startup
if __name__ == "__main__":
    import asyncio
    from fastmcp import FastMCP
    
    mcp = FastMCP("server-name")
    asyncio.run(mcp.run())
            """,
        },
        "deployment": {
            "docker_compose": """
# Docker Compose service definition
services:
  agent:
    build: .
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
      - mcp-servers
            """,
            "github_action": """
# CI/CD with GitHub Actions
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose up -d
            """,
        },
    }

    return snippets.get(component, {})


@mcp.tool()
async def analyze_dependencies() -> Dict[str, Any]:
    """
    Analyze project dependencies and their purposes

    Returns:
        Dependency analysis with versions and purposes
    """
    try:
        dependencies = {
            "agent": {
                "langchain": {
                    "version": "0.3.0",
                    "purpose": "LLM orchestration and agent framework",
                    "key_features": [
                        "Agent creation",
                        "Tool management",
                        "Memory systems",
                    ],
                },
                "chainlit": {
                    "version": "1.0.0",
                    "purpose": "Web-based chat UI",
                    "key_features": [
                        "Streaming responses",
                        "File uploads",
                        "Session management",
                    ],
                },
                "ollama": {
                    "version": "latest",
                    "purpose": "Local LLM hosting",
                    "key_features": [
                        "Model management",
                        "Inference API",
                        "GPU acceleration",
                    ],
                },
            },
            "mcp_servers": {
                "fastmcp": {
                    "version": "0.2.0",
                    "purpose": "MCP protocol implementation",
                    "key_features": [
                        "Tool registration",
                        "Async support",
                        "Type validation",
                    ],
                },
                "chromadb": {
                    "version": "0.4.0",
                    "purpose": "Vector database",
                    "key_features": [
                        "Embedding storage",
                        "Similarity search",
                        "Metadata filtering",
                    ],
                },
                "reportlab": {
                    "version": "4.0.0",
                    "purpose": "PDF generation",
                    "key_features": [
                        "Document creation",
                        "Styling",
                        "Layout management",
                    ],
                },
                "sentence-transformers": {
                    "version": "2.3.0",
                    "purpose": "Text embeddings",
                    "key_features": [
                        "Semantic search",
                        "Document encoding",
                        "Similarity computation",
                    ],
                },
            },
            "infrastructure": {
                "docker": {
                    "version": "24.0",
                    "purpose": "Containerization",
                    "key_features": [
                        "Isolation",
                        "Reproducibility",
                        "Resource management",
                    ],
                },
                "docker-compose": {
                    "version": "2.20",
                    "purpose": "Multi-container orchestration",
                    "key_features": [
                        "Service networking",
                        "Volume management",
                        "Dependency ordering",
                    ],
                },
            },
        }

        # Count total dependencies
        total_deps = sum(
            len(deps)
            for category in dependencies.values()
            for deps in category.values()
        )

        return {
            "status": "success",
            "total_dependencies": total_deps,
            "categories": dependencies,
            "recommendations": [
                "Keep dependencies updated for security",
                "Use virtual environments for Python packages",
                "Pin versions in production for stability",
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to analyze dependencies: {str(e)}",
        }


@mcp.tool()
async def get_deployment_instructions() -> Dict[str, Any]:
    """
    Get step-by-step deployment instructions

    Returns:
        Detailed deployment guide
    """
    return {
        "status": "success",
        "deployment_methods": {
            "local_development": {
                "steps": [
                    "Clone repository: git clone <repo-url>",
                    "Create .env file from .env.example",
                    "Build containers: docker-compose build",
                    "Start services: docker-compose up",
                    "Initialize data: docker exec agent python scripts/populate_vector_db.py",
                    "Access UI: http://localhost:8080",
                ],
                "requirements": ["Docker", "Docker Compose", "8GB+ RAM"],
                "estimated_time": "15 minutes",
            },
            "production_vps": {
                "steps": [
                    "Setup VPS with Ubuntu 22.04+",
                    "Install Docker and Docker Compose",
                    "Clone repository",
                    "Configure environment variables",
                    "Setup SSL with Traefik or Nginx",
                    "Deploy with docker-compose -f docker-compose.prod.yml up -d",
                    "Setup monitoring (optional)",
                    "Configure backups",
                ],
                "requirements": ["VPS with 4GB+ RAM", "Domain name", "SSL certificate"],
                "estimated_time": "1 hour",
            },
            "kubernetes": {
                "steps": [
                    "Build and push images to registry",
                    "Create Kubernetes manifests",
                    "Deploy ConfigMaps and Secrets",
                    "Deploy StatefulSets for databases",
                    "Deploy Deployments for services",
                    "Configure Ingress for external access",
                    "Setup monitoring with Prometheus",
                ],
                "requirements": ["Kubernetes cluster", "kubectl", "Container registry"],
                "estimated_time": "2-3 hours",
            },
        },
        "troubleshooting": {
            "common_issues": [
                {
                    "issue": "Ollama not responding",
                    "solution": "Ensure Ollama container is running and healthy",
                },
                {
                    "issue": "MCP tools not available",
                    "solution": "Check MCP server logs and network connectivity",
                },
                {
                    "issue": "Vector search returns no results",
                    "solution": "Run data population script to index documents",
                },
            ]
        },
    }
