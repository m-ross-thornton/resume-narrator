# mcp_servers/vector_db_server.py
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
from datetime import datetime
import numpy as np

mcp = FastMCP("vector-db-server")


class VectorSearchRequest(BaseModel):
    """Request model for vector search"""

    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata filters"
    )
    collection: str = Field(default="experience", description="Collection to search")
    include_metadata: bool = Field(
        default=True, description="Include metadata in results"
    )
    similarity_threshold: float = Field(
        default=0.7, description="Minimum similarity score"
    )


class DocumentIndexRequest(BaseModel):
    """Request model for indexing documents"""

    documents: List[str] = Field(..., description="List of documents to index")
    metadata: Optional[List[Dict]] = Field(
        default=None, description="Metadata for documents"
    )
    collection: str = Field(
        default="experience", description="Collection to index into"
    )
    chunk_size: int = Field(default=500, description="Chunk size for text splitting")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")


class VectorDBManager:
    """Manage ChromaDB collections and operations"""

    def __init__(self, persist_directory: str = "/app/data/embeddings/chroma_db"):
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Initialize embedding model (using a smaller model for local deployment)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Initialize collections
        self._init_collections()

    def _init_collections(self):
        """Initialize default collections"""
        collections = ["experience", "projects", "skills", "documents"]

        for collection_name in collections:
            try:
                self.client.create_collection(
                    name=collection_name, metadata={"hnsw:space": "cosine"}
                )
            except:
                # Collection already exists
                pass

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        embeddings = self.embedder.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """Search in a collection"""
        collection = self.client.get_collection(collection_name)

        # Generate query embedding
        query_embedding = self.embed_texts([query])[0]

        # Perform search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters if filters else None,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                    if results["metadatas"]
                    else {},
                    "similarity": 1
                    - results["distances"][0][i],  # Convert distance to similarity
                }
            )

        return formatted_results

    def index_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadata: Optional[List[Dict]] = None,
    ) -> int:
        """Index documents into a collection"""
        collection = self.client.get_collection(collection_name)

        # Generate embeddings
        embeddings = self.embed_texts(documents)

        # Generate IDs
        ids = [
            f"{collection_name}_{datetime.now().timestamp()}_{i}"
            for i in range(len(documents))
        ]

        # Add to collection
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadata if metadata else [{} for _ in documents],
            ids=ids,
        )

        return len(documents)


@mcp.tool()
async def search_experience(request: VectorSearchRequest) -> Dict[str, Any]:
    """
    Search through professional experience and projects

    Args:
        request: Search parameters including query, filters, and collection

    Returns:
        Search results with relevant documents and metadata
    """
    try:
        db_manager = VectorDBManager()

        results = db_manager.search(
            collection_name=request.collection,
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
        )

        # Filter by similarity threshold
        filtered_results = [
            r for r in results if r["similarity"] >= request.similarity_threshold
        ]

        if not request.include_metadata:
            for result in filtered_results:
                result.pop("metadata", None)

        return {
            "status": "success",
            "query": request.query,
            "collection": request.collection,
            "total_results": len(filtered_results),
            "results": filtered_results,
        }

    except Exception as e:
        return {"status": "error", "message": f"Search failed: {str(e)}", "results": []}


@mcp.tool()
async def index_experience_data(request: DocumentIndexRequest) -> Dict[str, Any]:
    """
    Index new documents into the vector database

    Args:
        request: Documents and metadata to index

    Returns:
        Indexing status and statistics
    """
    try:
        db_manager = VectorDBManager()

        # Chunk documents if needed
        chunked_docs = []
        chunked_metadata = []

        for i, doc in enumerate(request.documents):
            if len(doc) > request.chunk_size:
                # Simple chunking (you could use more sophisticated methods)
                chunks = [
                    doc[i : i + request.chunk_size]
                    for i in range(
                        0, len(doc), request.chunk_size - request.chunk_overlap
                    )
                ]
                chunked_docs.extend(chunks)

                # Duplicate metadata for each chunk
                if request.metadata and i < len(request.metadata):
                    chunk_metadata = request.metadata[i].copy()
                    chunk_metadata["chunk_index"] = list(range(len(chunks)))
                    chunked_metadata.extend([chunk_metadata] * len(chunks))
            else:
                chunked_docs.append(doc)
                if request.metadata and i < len(request.metadata):
                    chunked_metadata.append(request.metadata[i])

        # Index documents
        count = db_manager.index_documents(
            collection_name=request.collection,
            documents=chunked_docs,
            metadata=chunked_metadata if chunked_metadata else None,
        )

        return {
            "status": "success",
            "message": f"Indexed {count} document chunks",
            "collection": request.collection,
            "original_documents": len(request.documents),
            "chunks_created": count,
        }

    except Exception as e:
        return {"status": "error", "message": f"Indexing failed: {str(e)}"}


@mcp.tool()
async def get_similar_projects(project_name: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Find projects similar to a given project

    Args:
        project_name: Name of the project to find similar ones for
        top_k: Number of similar projects to return

    Returns:
        List of similar projects
    """
    try:
        db_manager = VectorDBManager()

        # First, find the project
        initial_results = db_manager.search(
            collection_name="projects", query=project_name, top_k=1
        )

        if not initial_results:
            return {"status": "error", "message": f"Project '{project_name}' not found"}

        # Use the project description to find similar ones
        project_desc = initial_results[0]["document"]

        similar = db_manager.search(
            collection_name="projects",
            query=project_desc,
            top_k=top_k + 1,  # +1 to exclude the original
        )

        # Remove the original project from results
        similar = [s for s in similar if s["id"] != initial_results[0]["id"]][:top_k]

        return {
            "status": "success",
            "original_project": project_name,
            "similar_projects": similar,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to find similar projects: {str(e)}",
        }


@mcp.tool()
async def analyze_skill_coverage() -> Dict[str, Any]:
    """
    Analyze skill coverage across all experiences and projects

    Returns:
        Skill analysis including frequency, categories, and gaps
    """
    try:
        db_manager = VectorDBManager()

        # Get all documents from experience and projects
        experience_collection = db_manager.client.get_collection("experience")
        projects_collection = db_manager.client.get_collection("projects")

        # Retrieve all documents
        exp_data = experience_collection.get(include=["documents", "metadatas"])
        proj_data = projects_collection.get(include=["documents", "metadatas"])

        # Extract skills from metadata
        skill_frequency = {}
        skill_categories = {"technical": [], "soft": [], "tools": [], "languages": []}

        for metadata in exp_data.get("metadatas", []):
            if metadata and "skills" in metadata:
                for skill in metadata["skills"]:
                    skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

        for metadata in proj_data.get("metadatas", []):
            if metadata and "technologies" in metadata:
                for tech in metadata["technologies"]:
                    skill_frequency[tech] = skill_frequency.get(tech, 0) + 1

        # Sort skills by frequency
        top_skills = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[
            :20
        ]

        return {
            "status": "success",
            "total_unique_skills": len(skill_frequency),
            "top_skills": dict(top_skills),
            "skill_categories": skill_categories,
            "analysis": {
                "most_used": top_skills[0][0] if top_skills else None,
                "skill_diversity": len(skill_frequency),
                "average_skill_frequency": sum(skill_frequency.values())
                / len(skill_frequency)
                if skill_frequency
                else 0,
            },
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to analyze skills: {str(e)}"}


# Add custom REST routes for HTTP API
from starlette.responses import JSONResponse
from starlette.requests import Request


@mcp.custom_route("/health", ["GET"])
async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "service": "vector-db-server"})


@mcp.custom_route("/tool/search_experience", ["POST"])
async def search_experience_endpoint(request: Request):
    """REST endpoint for searching experience"""
    try:
        data = await request.json()
        search_request = VectorSearchRequest(**data)
        result = await search_experience(search_request)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)


@mcp.custom_route("/tool/index_documents", ["POST"])
async def index_documents_endpoint(request: Request):
    """REST endpoint for indexing documents"""
    try:
        data = await request.json()
        index_request = DocumentIndexRequest(**data)
        result = await index_documents(index_request)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)


@mcp.custom_route("/tool/analyze_skills", ["POST"])
async def analyze_skills_endpoint(request: Request):
    """REST endpoint for analyzing skills"""
    try:
        result = await analyze_skill_coverage()
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)
