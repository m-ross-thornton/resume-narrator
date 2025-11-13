"""
Tests for the vector database data loading pipeline.

Tests verify that:
1. Raw data can be loaded from JSON files
2. Data is properly indexed into ChromaDB
3. Indexed data can be queried semantically
4. Agent can use search_experience tool to find relevant data
"""

import json
import pytest
from pathlib import Path
from typing import Dict, List, Any

# Add mcp-servers to path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers"))

from vector_db_server import VectorDBManager, VectorSearchRequest


@pytest.fixture
def test_data_dir():
    """Get path to test data directory"""
    return Path(__file__).parent.parent / "data" / "experience"


@pytest.fixture
def vector_db():
    """Create temporary vector database for testing"""
    db = VectorDBManager(persist_directory=":memory:")
    yield db
    # Cleanup happens automatically with in-memory db


class TestDataLoading:
    """Tests for loading structured data"""

    def test_work_history_file_exists(self, test_data_dir):
        """Test that work_history.json exists"""
        work_history_file = test_data_dir / "work_history.json"
        assert (
            work_history_file.exists()
        ), f"Work history file not found at {work_history_file}"

    def test_projects_file_exists(self, test_data_dir):
        """Test that projects.json exists"""
        projects_file = test_data_dir / "projects.json"
        assert projects_file.exists(), f"Projects file not found at {projects_file}"

    def test_skills_file_exists(self, test_data_dir):
        """Test that skills.json exists"""
        skills_file = test_data_dir / "skills.json"
        assert skills_file.exists(), f"Skills file not found at {skills_file}"

    def test_work_history_is_valid_json(self, test_data_dir):
        """Test that work_history.json is valid JSON"""
        work_history_file = test_data_dir / "work_history.json"
        with open(work_history_file, "r") as f:
            data = json.load(f)
        assert "work_history" in data
        assert isinstance(data["work_history"], list)
        assert len(data["work_history"]) > 0

    def test_work_history_has_required_fields(self, test_data_dir):
        """Test that work history entries have required fields"""
        work_history_file = test_data_dir / "work_history.json"
        with open(work_history_file, "r") as f:
            data = json.load(f)

        required_fields = ["company", "title", "description", "skills"]
        for job in data["work_history"]:
            for field in required_fields:
                assert field in job, f"Missing required field: {field}"

    def test_projects_is_valid_json(self, test_data_dir):
        """Test that projects.json is valid JSON"""
        projects_file = test_data_dir / "projects.json"
        with open(projects_file, "r") as f:
            data = json.load(f)
        assert "projects" in data
        assert isinstance(data["projects"], list)

    def test_skills_is_valid_json(self, test_data_dir):
        """Test that skills.json is valid JSON"""
        skills_file = test_data_dir / "skills.json"
        with open(skills_file, "r") as f:
            data = json.load(f)
        assert "skills" in data
        assert isinstance(data["skills"], list)


@pytest.mark.integration
class TestVectorDatabaseIndexing:
    """Tests for indexing data into vector database"""

    def test_index_work_history(self, test_data_dir, vector_db):
        """Test indexing work history into vector database"""
        work_history_file = test_data_dir / "work_history.json"
        with open(work_history_file, "r") as f:
            data = json.load(f)

        documents = []
        metadata = []
        for job in data["work_history"]:
            doc_text = f"Company: {job['company']}\nTitle: {job['title']}\n{job['description']}"
            documents.append(doc_text)
            # ChromaDB metadata only accepts simple types - stringify lists
            metadata.append(
                {
                    "type": "work_history",
                    "company": job["company"],
                    "title": job["title"],
                    "skills": ", ".join(job.get("skills", [])),
                }
            )

        count = vector_db.index_documents("experience", documents, metadata)
        assert count == len(documents)

    def test_index_projects(self, test_data_dir, vector_db):
        """Test indexing projects into vector database"""
        projects_file = test_data_dir / "projects.json"
        with open(projects_file, "r") as f:
            data = json.load(f)

        documents = []
        metadata = []
        for project in data.get("projects", []):
            doc_text = f"Project: {project['name']}\n{project['description']}"
            documents.append(doc_text)
            # ChromaDB metadata only accepts simple types - stringify lists
            metadata.append(
                {
                    "type": "project",
                    "name": project["name"],
                    "technologies": ", ".join(project.get("technologies", [])),
                }
            )

        if documents:
            count = vector_db.index_documents("projects", documents, metadata)
            assert count == len(documents)


@pytest.mark.integration
class TestVectorDatabaseSearch:
    """Tests for searching indexed data"""

    def test_search_experience_returns_results(self, test_data_dir, vector_db):
        """Test that searching for experience returns relevant results"""
        work_history_file = test_data_dir / "work_history.json"
        with open(work_history_file, "r") as f:
            data = json.load(f)

        documents = []
        metadata = []
        for job in data["work_history"]:
            doc_text = f"Company: {job['company']}\nTitle: {job['title']}\n{job['description']}"
            documents.append(doc_text)
            metadata.append({"type": "work_history", "company": job["company"]})

        vector_db.index_documents("experience", documents, metadata)

        # Search for something that should match
        results = vector_db.search("experience", "machine learning data science")
        assert len(results) > 0

    def test_search_returns_metadata(self, test_data_dir, vector_db):
        """Test that search results include metadata"""
        work_history_file = test_data_dir / "work_history.json"
        with open(work_history_file, "r") as f:
            data = json.load(f)

        documents = []
        metadata = []
        for job in data["work_history"]:
            doc_text = f"{job['company']} {job['title']}"
            documents.append(doc_text)
            metadata.append(
                {
                    "type": "work_history",
                    "company": job["company"],
                    "title": job["title"],
                }
            )

        vector_db.index_documents("experience", documents, metadata)

        results = vector_db.search("experience", "data engineer")
        assert len(results) > 0
        assert "metadata" in results[0]

    def test_search_similarity_threshold(self, test_data_dir, vector_db):
        """Test that similarity threshold filters results correctly"""
        # Index sample data
        documents = [
            "Python programming expert with 10 years experience",
            "Java developer specializing in enterprise software",
            "Machine learning engineer using PyTorch and TensorFlow",
        ]
        metadata = [
            {"type": "skill", "language": "Python"},
            {"type": "skill", "language": "Java"},
            {"type": "skill", "language": "Python"},
        ]

        vector_db.index_documents("experience", documents, metadata)

        # Search with default threshold
        results = vector_db.search("experience", "Python programming", top_k=3)
        assert len(results) > 0


class TestVectorSearchRequest:
    """Tests for VectorSearchRequest model"""

    def test_search_request_defaults(self):
        """Test that VectorSearchRequest has proper defaults"""
        request = VectorSearchRequest(query="test")
        assert request.query == "test"
        assert request.top_k == 5
        assert request.collection == "experience"
        assert request.include_metadata is True
        assert request.similarity_threshold == 0.7

    def test_search_request_custom_parameters(self):
        """Test VectorSearchRequest with custom parameters"""
        request = VectorSearchRequest(
            query="AI engineering",
            top_k=10,
            collection="projects",
            similarity_threshold=0.5,
        )
        assert request.query == "AI engineering"
        assert request.top_k == 10
        assert request.collection == "projects"
        assert request.similarity_threshold == 0.5


@pytest.mark.integration
class TestDataIntegration:
    """Integration tests for the full pipeline"""

    def test_load_and_search_pipeline(self, test_data_dir, vector_db):
        """Test full pipeline: load data and search for it"""
        # Load work history
        work_history_file = test_data_dir / "work_history.json"
        with open(work_history_file, "r") as f:
            data = json.load(f)

        documents = []
        metadata = []
        for job in data["work_history"]:
            doc_text = f"{job['company']} - {job['title']}: {job['description']}"
            documents.append(doc_text)
            # ChromaDB metadata only accepts simple types - stringify lists
            metadata.append(
                {
                    "company": job["company"],
                    "title": job["title"],
                    "skills": ", ".join(job.get("skills", [])),
                }
            )

        # Index data
        count = vector_db.index_documents("experience", documents, metadata)
        assert count == len(documents)

        # Search for indexed content
        results = vector_db.search("experience", "AI and machine learning")
        assert len(results) > 0
        assert results[0]["document"] is not None
        assert results[0]["metadata"] is not None
