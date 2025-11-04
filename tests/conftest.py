"""Pytest configuration and fixtures for Resnar tests"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Environment variables for testing
os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
os.environ.setdefault("CHROMA_HOST", "http://localhost:8000")
os.environ.setdefault("MCP_RESUME_URL", "http://localhost:9001")
os.environ.setdefault("MCP_VECTOR_URL", "http://localhost:9002")
os.environ.setdefault("MCP_CODE_URL", "http://localhost:9003")
os.environ.setdefault("SUBJECT_NAME", "Ross")


@pytest.fixture
def test_data_path():
    """Return path to test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_resume_data():
    """Mock resume data for testing"""
    return {
        "contact": {
            "name": "Ross",
            "email": "ross@example.com",
            "phone": "(555) 123-4567",
            "location": "San Francisco, CA",
        },
        "summary": "Experienced software engineer with expertise in Python and AI",
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Tech Co",
                "duration": "2020-present",
                "description": "Led AI and ML projects",
            }
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "school": "State University",
                "year": "2018",
            }
        ],
        "skills": ["Python", "LLMs", "FastAPI", "React"],
    }


@pytest.fixture
def mock_experience_documents():
    """Mock experience documents for vector search"""
    return [
        "Developed a Python FastAPI backend for a real-time data processing system",
        "Led a team of engineers in building a machine learning pipeline using LangChain",
        "Created an interactive React dashboard for monitoring system metrics",
        "Implemented vector similarity search using ChromaDB and sentence transformers",
        "Designed and deployed Docker containers for microservices architecture",
    ]


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async (deselect with '-m \"not asyncio\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests that require running services"
    )
    config.addinivalue_line("markers", "unit: marks tests as unit only")
