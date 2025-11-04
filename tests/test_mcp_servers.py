"""Tests for MCP servers"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestResumePDFServer:
    """Test Resume PDF generation server"""

    @pytest.mark.unit
    def test_resume_request_model(self):
        """Test ResumeRequest model validation"""
        from mcp_servers.resume_pdf_server import ResumeRequest

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
        from mcp_servers.resume_pdf_server import ResumeRequest

        request = ResumeRequest()

        assert request.template == "professional"
        assert len(request.sections) >= 4
        assert isinstance(request.format_options, dict)

    @pytest.mark.unit
    def test_resume_template_validation(self):
        """Test resume template options"""
        from mcp_servers.resume_pdf_server import ResumeRequest

        templates = ["professional", "creative", "technical", "executive"]
        for template in templates:
            request = ResumeRequest(template=template)
            assert request.template == template

    @pytest.mark.unit
    def test_resume_data_class(self):
        """Test ResumeData class loading"""
        from mcp_servers.resume_pdf_server import ResumeData

        # This will fail if resume_data.json doesn't exist, which is expected
        with pytest.raises(FileNotFoundError):
            data = ResumeData(data_path="/nonexistent/path")

    @pytest.mark.unit
    def test_resume_request_custom_output_filename(self):
        """Test custom output filename in ResumeRequest"""
        from mcp_servers.resume_pdf_server import ResumeRequest

        request = ResumeRequest(output_filename="custom_resume.pdf")

        assert request.output_filename == "custom_resume.pdf"


class TestVectorDBServer:
    """Test Vector DB server"""

    @pytest.mark.unit
    def test_vector_search_request_model(self):
        """Test VectorSearchRequest model validation"""
        from mcp_servers.vector_db_server import VectorSearchRequest

        request = VectorSearchRequest(query="python projects")

        assert request.query == "python projects"
        assert request.top_k == 5
        assert request.collection == "experience"
        assert request.similarity_threshold == 0.7

    @pytest.mark.unit
    def test_vector_search_custom_parameters(self):
        """Test VectorSearchRequest with custom parameters"""
        from mcp_servers.vector_db_server import VectorSearchRequest

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
        from mcp_servers.vector_db_server import DocumentIndexRequest

        documents = ["Document 1", "Document 2"]
        request = DocumentIndexRequest(documents=documents)

        assert request.documents == documents
        assert request.collection == "experience"
        assert request.chunk_size == 500
        assert request.chunk_overlap == 50

    @pytest.mark.unit
    def test_document_index_with_metadata(self):
        """Test DocumentIndexRequest with metadata"""
        from mcp_servers.vector_db_server import DocumentIndexRequest

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
        from mcp_servers.vector_db_server import VectorDBManager

        # This will try to create a client - may fail without ChromaDB running
        with patch("chromadb.PersistentClient") as mock_chroma:
            mock_chroma.return_value = MagicMock()
            with patch("sentence_transformers.SentenceTransformer"):
                manager = VectorDBManager(persist_directory="/tmp/test_db")

                assert manager.persist_directory == "/tmp/test_db"
                mock_chroma.assert_called_once()

    @pytest.mark.unit
    def test_similarity_threshold_validation(self):
        """Test similarity threshold is between 0 and 1"""
        from mcp_servers.vector_db_server import VectorSearchRequest

        # Valid thresholds
        for threshold in [0.0, 0.5, 0.9, 1.0]:
            request = VectorSearchRequest(query="test", similarity_threshold=threshold)
            assert 0.0 <= request.similarity_threshold <= 1.0

    @pytest.mark.unit
    def test_top_k_positive(self):
        """Test top_k must be positive"""
        from mcp_servers.vector_db_server import VectorSearchRequest

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
            from mcp_servers.code_explorer_server import mcp as code_mcp

            assert code_mcp is not None
        except ImportError as e:
            pytest.fail(f"Failed to import code explorer server: {e}")

    @pytest.mark.unit
    def test_code_explorer_has_mcp_instance(self):
        """Test code explorer has FastMCP instance"""
        from mcp_servers.code_explorer_server import mcp

        assert mcp is not None
        assert hasattr(mcp, "run")


class TestMCPServerIntegration:
    """Test MCP server integration"""

    @pytest.mark.unit
    def test_all_servers_importable(self):
        """Test all MCP servers can be imported"""
        servers = [
            "mcp_servers.resume_pdf_server",
            "mcp_servers.vector_db_server",
            "mcp_servers.code_explorer_server",
        ]

        for server_module in servers:
            try:
                __import__(server_module)
            except ImportError as e:
                pytest.fail(f"Failed to import {server_module}: {e}")

    @pytest.mark.unit
    def test_server_runner_exists(self):
        """Test server runner script exists"""
        from mcp_servers.server_runner import MCPServerManager

        assert MCPServerManager is not None

    @pytest.mark.unit
    def test_mcp_server_manager_initialization(self):
        """Test MCPServerManager initializes correctly"""
        from mcp_servers.server_runner import MCPServerManager

        manager = MCPServerManager()

        assert manager.servers is not None
        assert len(manager.servers) >= 3
        assert "resume" in manager.servers
        assert "vector" in manager.servers
        assert "code" in manager.servers
