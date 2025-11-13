"""Tests for MCP servers"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import importlib.util

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def import_mcp_module(module_name):
    """Import a module from mcp-servers directory (with hyphen)

    Mock external dependencies that may not be installed during testing.
    """
    # Mock external dependencies before importing
    from unittest.mock import MagicMock, Mock

    # Pre-mock modules that might not be installed or slow to import
    # Create proper mock packages with submodules
    mock_modules = [
        "fastmcp",
        "chromadb",
        "chromadb.config",
        "sentence_transformers",
        "reportlab",
        "reportlab.lib",
        "reportlab.lib.pagesizes",
        "reportlab.lib.styles",
        "reportlab.lib.units",
        "reportlab.lib.enums",
        "reportlab.lib.colors",
        "reportlab.platypus",
        "pypdf",
        "docx",
        "python_docx",
    ]

    # Create all mock modules with proper package hierarchy
    mock_objects = {}
    for mod_name in sorted(mock_modules):
        if mod_name not in sys.modules:
            mock_objects[mod_name] = MagicMock()
            sys.modules[mod_name] = mock_objects[mod_name]

    mcp_servers_dir = Path(__file__).parent.parent / "mcp-servers"
    module_file = mcp_servers_dir / f"{module_name}.py"

    if not module_file.exists():
        raise ModuleNotFoundError(f"Cannot find {module_file}")

    spec = importlib.util.spec_from_file_location(module_name, module_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestResumePDFServer:
    """Test Resume PDF generation server"""

    @pytest.mark.unit
    def test_resume_request_model(self):
        """Test ResumeRequest model validation"""
        resume_pdf_server = import_mcp_module("resume_pdf_server")
        ResumeRequest = resume_pdf_server.ResumeRequest

        request = ResumeRequest(
            template="professional",
            sections=["contact", "experience"],
        )

        assert request.template == "professional"
        assert "contact" in request.sections
        assert "experience" in request.sections

    @pytest.mark.unit
    def test_resume_request_defaults(self):
        """Test ResumeRequest has sensible defaults"""
        resume_pdf_server = import_mcp_module("resume_pdf_server")
        ResumeRequest = resume_pdf_server.ResumeRequest

        request = ResumeRequest()

        assert request.template == "professional"
        assert len(request.sections) >= 4
        assert isinstance(request.format_options, dict)

    @pytest.mark.unit
    def test_resume_template_validation(self):
        """Test resume template options"""
        resume_pdf_server = import_mcp_module("resume_pdf_server")
        ResumeRequest = resume_pdf_server.ResumeRequest

        templates = ["professional", "creative", "technical", "executive"]
        for template in templates:
            request = ResumeRequest(template=template)
            assert request.template == template

    @pytest.mark.unit
    def test_resume_data_class(self):
        """Test ResumeData class loading"""
        resume_pdf_server = import_mcp_module("resume_pdf_server")
        ResumeData = resume_pdf_server.ResumeData

        # This will fail if resume_data.json doesn't exist, which is expected
        with pytest.raises(FileNotFoundError):
            data = ResumeData(data_path="/nonexistent/path")

    @pytest.mark.unit
    def test_resume_request_custom_output_filename(self):
        """Test custom output filename in ResumeRequest"""
        resume_pdf_server = import_mcp_module("resume_pdf_server")
        ResumeRequest = resume_pdf_server.ResumeRequest

        request = ResumeRequest(output_filename="custom_resume.pdf")

        assert request.output_filename == "custom_resume.pdf"


class TestVectorDBServer:
    """Test Vector DB server"""

    @pytest.mark.unit
    def test_vector_search_request_model(self):
        """Test VectorSearchRequest model validation"""
        vector_db_server = import_mcp_module("vector_db_server")
        VectorSearchRequest = vector_db_server.VectorSearchRequest

        request = VectorSearchRequest(query="python projects")

        assert request.query == "python projects"
        assert request.top_k == 5
        assert request.collection == "experience"
        assert request.similarity_threshold == 0.7

    @pytest.mark.unit
    def test_vector_search_custom_parameters(self):
        """Test VectorSearchRequest with custom parameters"""
        vector_db_server = import_mcp_module("vector_db_server")
        VectorSearchRequest = vector_db_server.VectorSearchRequest

        request = VectorSearchRequest(
            query="machine learning",
            top_k=10,
            collection="projects",
            similarity_threshold=0.8,
        )

        assert request.query == "machine learning"
        assert request.top_k == 10
        assert request.collection == "projects"
        assert request.similarity_threshold == 0.8

    @pytest.mark.unit
    def test_document_index_request_model(self):
        """Test DocumentIndexRequest model validation"""
        vector_db_server = import_mcp_module("vector_db_server")
        DocumentIndexRequest = vector_db_server.DocumentIndexRequest

        documents = ["Document 1", "Document 2"]
        request = DocumentIndexRequest(documents=documents)

        assert request.documents == documents
        assert request.collection == "experience"
        assert request.chunk_size == 500
        assert request.chunk_overlap == 50

    @pytest.mark.unit
    def test_document_index_with_metadata(self):
        """Test DocumentIndexRequest with metadata"""
        vector_db_server = import_mcp_module("vector_db_server")
        DocumentIndexRequest = vector_db_server.DocumentIndexRequest

        documents = ["Doc1", "Doc2"]
        metadata = [
            {"source": "resume", "date": "2024-01-01"},
            {"source": "portfolio", "date": "2024-01-02"},
        ]

        request = DocumentIndexRequest(documents=documents, metadata=metadata)

        assert len(request.documents) == len(request.metadata)
        assert request.metadata[0]["source"] == "resume"

    @pytest.mark.unit
    def test_vector_db_manager_initialization(self):
        """Test VectorDBManager initialization"""
        vector_db_server = import_mcp_module("vector_db_server")
        VectorDBManager = vector_db_server.VectorDBManager

        # VectorDBManager now uses httpx.Client to call remote ChromaDB
        with patch("httpx.Client"):
            with patch("sentence_transformers.SentenceTransformer"):
                manager = VectorDBManager(persist_directory="/tmp/test_db")

                assert manager.persist_directory == "/tmp/test_db"
                assert manager.chromadb_url == "http://chromadb:8000/api/v1"

    @pytest.mark.unit
    def test_similarity_threshold_validation(self):
        """Test similarity threshold is between 0 and 1"""
        vector_db_server = import_mcp_module("vector_db_server")
        VectorSearchRequest = vector_db_server.VectorSearchRequest

        # Valid thresholds
        for threshold in [0.0, 0.5, 0.9, 1.0]:
            request = VectorSearchRequest(query="test", similarity_threshold=threshold)
            assert 0.0 <= request.similarity_threshold <= 1.0

    @pytest.mark.unit
    def test_top_k_positive(self):
        """Test top_k must be positive"""
        vector_db_server = import_mcp_module("vector_db_server")
        VectorSearchRequest = vector_db_server.VectorSearchRequest

        request = VectorSearchRequest(query="test", top_k=1)
        assert request.top_k > 0

    @pytest.mark.integration
    def test_vector_db_connection(self):
        """Test connection to vector DB (requires ChromaDB running)"""
        pytest.skip("Requires ChromaDB running")


class TestCodeExplorerServer:
    """Test Code Explorer server"""

    @pytest.mark.unit
    def test_code_explorer_import(self):
        """Test code explorer server can be imported"""
        try:
            code_explorer_server = import_mcp_module("code_explorer_server")
            code_mcp = code_explorer_server.mcp

            assert code_mcp is not None
        except ImportError as e:
            pytest.fail(f"Failed to import code explorer server: {e}")

    @pytest.mark.unit
    def test_code_explorer_has_mcp_instance(self):
        """Test code explorer has FastMCP instance"""
        code_explorer_server = import_mcp_module("code_explorer_server")
        mcp = code_explorer_server.mcp

        assert mcp is not None
        assert hasattr(mcp, "run")


class TestMCPServerIntegration:
    """Test MCP server integration"""

    @pytest.mark.unit
    def test_all_servers_importable(self):
        """Test all MCP servers can be imported"""
        servers = [
            "resume_pdf_server",
            "vector_db_server",
            "code_explorer_server",
        ]

        for server_name in servers:
            try:
                import_mcp_module(server_name)
            except Exception as e:
                pytest.fail(f"Failed to import {server_name}: {e}")
