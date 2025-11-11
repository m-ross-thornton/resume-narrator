#!/usr/bin/env python3
"""
Data loading script for populating the vector database with experience data.

This script reads structured JSON files from /data/experience/ and indexes them
into the ChromaDB vector database for semantic search by the agent.

Usage:
    python scripts/load_experience_to_vector_db.py [--collections COLLECTION] [--reset]

Examples:
    # Load all collections
    python scripts/load_experience_to_vector_db.py

    # Load only work history
    python scripts/load_experience_to_vector_db.py --collections work_history

    # Reset and reload all data
    python scripts/load_experience_to_vector_db.py --reset
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import argparse
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-servers"))

from vector_db_server import VectorDBManager

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent / "experience"
CHROMA_DB_PATH = Path(__file__).parent / "embeddings" / "chroma_db"


def load_work_history() -> tuple[List[str], List[Dict[str, Any]]]:
    """Load work history from work_history.json"""
    work_history_file = DATA_DIR / "work_history.json"

    if not work_history_file.exists():
        logger.warning(f"Work history file not found: {work_history_file}")
        return [], []

    with open(work_history_file, "r") as f:
        data = json.load(f)

    documents = []
    metadata = []

    for job in data.get("work_history", []):
        # Create comprehensive document combining title, company, and description
        doc_text = f"""
Company: {job.get('company', 'N/A')}
Title: {job.get('title', 'N/A')}
Duration: {job.get('duration', 'N/A')}

Description:
{job.get('description', '')}

Key Achievements:
{chr(10).join('- ' + a for a in job.get('achievements', []))}

Skills Applied:
{', '.join(job.get('skills', []))}
        """.strip()

        documents.append(doc_text)
        # ChromaDB metadata only accepts strings, ints, floats, bools - not lists
        # So we stringify lists
        metadata.append(
            {
                "type": "work_history",
                "company": job.get("company"),
                "title": job.get("title"),
                "duration": job.get("duration"),
                "skills": ", ".join(job.get("skills", [])),
                "achievements_count": str(len(job.get("achievements", []))),
            }
        )

    logger.info(f"Loaded {len(documents)} work history entries")
    return documents, metadata


def load_projects() -> tuple[List[str], List[Dict[str, Any]]]:
    """Load projects from projects.json"""
    projects_file = DATA_DIR / "projects.json"

    if not projects_file.exists():
        logger.warning(f"Projects file not found: {projects_file}")
        return [], []

    with open(projects_file, "r") as f:
        data = json.load(f)

    documents = []
    metadata = []

    for project in data.get("projects", []):
        # Create comprehensive document
        doc_text = f"""
Project: {project.get('name', 'N/A')}
Role: {project.get('role', 'N/A')}
Duration: {project.get('duration', 'N/A')}

Description:
{project.get('description', '')}

Technologies Used:
{', '.join(project.get('technologies', []))}

Key Achievements:
{chr(10).join('- ' + a for a in project.get('achievements', []))}
        """.strip()

        documents.append(doc_text)
        # ChromaDB metadata only accepts strings, ints, floats, bools - not lists
        # So we stringify lists
        metadata.append(
            {
                "type": "project",
                "name": project.get("name"),
                "role": project.get("role"),
                "duration": project.get("duration"),
                "technologies": ", ".join(project.get("technologies", [])),
                "achievements_count": str(len(project.get("achievements", []))),
            }
        )

    logger.info(f"Loaded {len(documents)} projects")
    return documents, metadata


def load_skills() -> tuple[List[str], List[Dict[str, Any]]]:
    """Load skills from skills.json"""
    skills_file = DATA_DIR / "skills.json"

    if not skills_file.exists():
        logger.warning(f"Skills file not found: {skills_file}")
        return [], []

    with open(skills_file, "r") as f:
        data = json.load(f)

    documents = []
    metadata = []

    for skill_entry in data.get("skills", []):
        # Create document for each skill category
        category = skill_entry.get("category", "General")
        skill_list = skill_entry.get("skills", [])

        doc_text = f"""
Skill Category: {category}

Skills:
{chr(10).join('- ' + s for s in skill_list)}

Proficiency: {skill_entry.get('proficiency_level', 'Not specified')}
Experience: {skill_entry.get('years_of_experience', 'Not specified')} years
        """.strip()

        documents.append(doc_text)
        # ChromaDB metadata only accepts strings, ints, floats, bools - not lists
        # So we stringify lists
        metadata.append(
            {
                "type": "skills",
                "category": category,
                "skills": ", ".join(skill_list),
                "proficiency_level": str(skill_entry.get("proficiency_level", "")),
                "years_of_experience": str(skill_entry.get("years_of_experience", "")),
            }
        )

    logger.info(f"Loaded {len(documents)} skill categories")
    return documents, metadata


def index_collection(
    db_manager: VectorDBManager,
    collection_name: str,
    documents: List[str],
    metadata: List[Dict[str, Any]],
) -> bool:
    """Index documents into a specific collection"""
    if not documents:
        logger.warning(f"No documents to index for collection: {collection_name}")
        return False

    try:
        count = db_manager.index_documents(
            collection_name=collection_name,
            documents=documents,
            metadata=metadata if metadata else None,
        )
        logger.info(
            f"Successfully indexed {count} documents to '{collection_name}' collection"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to index documents to '{collection_name}': {str(e)}")
        return False


def main():
    """Main data loading function"""
    parser = argparse.ArgumentParser(
        description="Load experience data into vector database"
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        choices=["work_history", "projects", "skills"],
        default=["work_history", "projects", "skills"],
        help="Which collections to load (default: all)",
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset database before loading"
    )
    parser.add_argument(
        "--chroma-path",
        type=str,
        default=str(CHROMA_DB_PATH),
        help="Path to ChromaDB directory",
    )

    args = parser.parse_args()

    logger.info("Starting vector database population...")
    logger.info(f"Collections to load: {args.collections}")

    # Initialize database manager
    try:
        db_manager = VectorDBManager(persist_directory=args.chroma_path)
        logger.info(f"Connected to ChromaDB at {args.chroma_path}")
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {str(e)}")
        return 1

    # Reset if requested
    if args.reset:
        logger.warning("Resetting database...")
        try:
            db_manager.client.reset()
            logger.info("Database reset complete")
            # Reinitialize collections
            db_manager._init_collections()
        except Exception as e:
            logger.error(f"Failed to reset database: {str(e)}")
            return 1

    # Load collections
    success_count = 0
    total_count = len(args.collections)

    if "work_history" in args.collections:
        logger.info("\n--- Loading Work History ---")
        docs, meta = load_work_history()
        if index_collection(db_manager, "experience", docs, meta):
            success_count += 1

    if "projects" in args.collections:
        logger.info("\n--- Loading Projects ---")
        docs, meta = load_projects()
        if index_collection(db_manager, "projects", docs, meta):
            success_count += 1

    if "skills" in args.collections:
        logger.info("\n--- Loading Skills ---")
        docs, meta = load_skills()
        if index_collection(db_manager, "skills", docs, meta):
            success_count += 1

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info(
        f"Data loading complete: {success_count}/{total_count} collections loaded"
    )

    if success_count == total_count:
        logger.info("✓ All collections loaded successfully")
        return 0
    else:
        logger.warning(f"⚠ {total_count - success_count} collection(s) failed to load")
        return 1


if __name__ == "__main__":
    sys.exit(main())
