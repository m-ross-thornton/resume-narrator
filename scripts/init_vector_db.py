#!/usr/bin/env python3
"""
Hybrid initialization script for vector database population.

This script implements the "hybrid initialization" approach:
- Checks if vector DB collections contain data
- If empty: runs populate_experience_data.py and load_experience_to_vector_db.py
- If populated: skips initialization for fast restarts
- Allows manual control and supports CI/CD pipelines

Usage:
    # Auto-detect and initialize if needed
    python scripts/init_vector_db.py

    # Force re-initialization (reset vector DB)
    python scripts/init_vector_db.py --force

    # Check status without initializing
    python scripts/init_vector_db.py --check-only

    # Docker: Optional init service that runs before vector server
    docker compose run --rm init_vector_db
"""

import sys
import logging
import argparse
import subprocess
import json
from pathlib import Path
from typing import Tuple, Dict, Any
import time

# Try to import chromadb for checking existing data
try:
    import chromadb
    from chromadb.config import Settings

    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VectorDBInitializer:
    """Initialize vector database with experience data"""

    def __init__(
        self,
        data_dir: str = "data",
        chroma_path: str = None,
        chroma_host: str = None,
    ):
        """
        Initialize the VectorDBInitializer.

        Args:
            data_dir: Base data directory path
            chroma_path: Path to persisted ChromaDB (local mode)
            chroma_host: Host URL for ChromaDB server (remote mode)
        """
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.experience_dir = self.data_dir / "experience"
        self.embeddings_dir = self.data_dir / "embeddings"

        # ChromaDB configuration
        self.chroma_path = chroma_path or str(self.embeddings_dir / "chroma_db")
        self.chroma_host = chroma_host

        # Ensure directories exist
        self.experience_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized with data_dir: {self.data_dir}")
        logger.info(f"ChromaDB path: {self.chroma_path}")

    def check_collections_populated(self) -> Tuple[bool, Dict[str, int]]:
        """
        Check if vector DB collections are populated with data.

        Returns:
            Tuple of (is_populated: bool, collection_counts: Dict[str, int])
        """
        if not HAS_CHROMADB:
            logger.warning("⚠ chromadb not available, cannot check collection status")
            return False, {}

        try:
            # Connect to ChromaDB
            client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # Check each collection
            collection_counts = {}
            for collection_name in ["experience", "projects", "skills"]:
                try:
                    collection = client.get_collection(collection_name)
                    count = collection.count()
                    collection_counts[collection_name] = count
                    logger.info(f"  {collection_name}: {count} documents")
                except Exception as e:
                    logger.debug(f"Could not get collection {collection_name}: {e}")
                    collection_counts[collection_name] = 0

            # Consider populated if any main collection has data
            is_populated = any(
                count > 0
                for name, count in collection_counts.items()
                if name in ["experience", "projects"]
            )

            return is_populated, collection_counts

        except Exception as e:
            logger.warning(f"⚠ Could not check ChromaDB status: {e}")
            return False, {}

    def check_raw_data_exists(self) -> bool:
        """Check if raw data files exist for population."""
        pdf_files = list(self.raw_dir.glob("*.pdf"))
        csv_file = self.raw_dir / "Profile.csv"

        has_pdf = len(pdf_files) > 0
        has_csv = csv_file.exists()

        logger.info(f"Raw data check:")
        logger.info(f"  PDF files: {len(pdf_files)} found")
        logger.info(f"  CSV profile: {'found' if has_csv else 'not found'}")

        return has_pdf or has_csv

    def check_structured_data_exists(self) -> Dict[str, bool]:
        """Check if structured JSON data exists."""
        files = {
            "work_history": self.experience_dir / "work_history.json",
            "projects": self.experience_dir / "projects.json",
            "skills": self.experience_dir / "skills.json",
        }

        status = {}
        for name, path in files.items():
            exists = path.exists()
            if exists:
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        # Check if data is not empty
                        key = list(data.keys())[0] if data else None
                        has_content = key and len(data[key]) > 0
                    status[name] = has_content
                    logger.info(f"  {name}: exists with content")
                except Exception as e:
                    logger.warning(f"  {name}: exists but invalid - {e}")
                    status[name] = False
            else:
                status[name] = False
                logger.info(f"  {name}: not found")

        return status

    def run_populate_experience(self) -> bool:
        """
        Run populate_experience_data.py script.

        Returns:
            True if successful, False otherwise
        """
        logger.info("\n📝 Stage 1: Populating structured experience data...")

        script_path = Path(__file__).parent / "populate_experience_data.py"
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.data_dir.parent,
                timeout=600,  # 10 minutes timeout
                capture_output=False,
            )

            if result.returncode == 0:
                logger.info("✓ Successfully populated structured data")
                return True
            else:
                logger.error(
                    f"✗ populate_experience_data.py failed with return code {result.returncode}"
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error("✗ populate_experience_data.py timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"✗ Error running populate_experience_data.py: {e}")
            return False

    def run_load_to_vector_db(self, reset: bool = False) -> bool:
        """
        Run load_experience_to_vector_db.py script.

        Args:
            reset: If True, reset vector DB collections before loading

        Returns:
            True if successful, False otherwise
        """
        logger.info("\n🗂️  Stage 2: Indexing data into vector database...")

        script_path = Path(__file__).parent / "load_experience_to_vector_db.py"
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False

        try:
            cmd = [
                sys.executable,
                str(script_path),
                "--collections",
                "work_history",
                "projects",
                "skills",
                "--chroma-path",
                self.chroma_path,
            ]

            if reset:
                cmd.append("--reset")

            result = subprocess.run(
                cmd,
                cwd=self.data_dir.parent,
                timeout=600,  # 10 minutes timeout
                capture_output=False,
            )

            if result.returncode == 0:
                logger.info("✓ Successfully indexed data into vector database")
                return True
            else:
                logger.error(
                    f"✗ load_experience_to_vector_db.py failed with return code {result.returncode}"
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error("✗ load_experience_to_vector_db.py timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"✗ Error running load_experience_to_vector_db.py: {e}")
            return False

    def initialize(self, force: bool = False) -> bool:
        """
        Run full initialization pipeline.

        Args:
            force: If True, reinitialize even if data exists

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("Vector DB Initialization - Hybrid Approach")
        logger.info("=" * 60)

        # Check current status
        logger.info("\n📊 Checking current state...\n")

        is_populated, collection_counts = self.check_collections_populated()
        logger.info(
            f"\nVector DB Status: {'✓ Populated' if is_populated else '⚠ Empty'}"
        )
        for name, count in collection_counts.items():
            logger.info(f"  - {name}: {count} documents")

        # If populated and not forced, skip initialization
        if is_populated and not force:
            logger.info("\n✅ Vector DB already populated, skipping initialization")
            logger.info("   (Use --force to reinitialize)\n")
            return True

        if force:
            logger.info("\n⚡ Force flag set, reinitializing...")

        # Check for raw data
        logger.info("\nChecking for raw data...")
        has_raw = self.check_raw_data_exists()
        if not has_raw:
            logger.warning(
                "⚠ No raw data found (PDF or CSV). "
                "Please add files to data/raw/ directory"
            )

        # Check for structured data
        logger.info("\nChecking for structured experience data...")
        structured_status = self.check_structured_data_exists()

        # Determine what needs to be done
        needs_populate = (
            has_raw and not all(structured_status.values()) or (force and has_raw)
        )
        needs_index = force or not is_populated

        if not needs_populate and not needs_index:
            logger.info("\n✅ All data already prepared, skipping initialization\n")
            return True

        # Run initialization stages
        if needs_populate:
            if not self.run_populate_experience():
                logger.error("❌ Failed to populate structured data")
                return False

        if needs_index:
            if not self.run_load_to_vector_db(reset=force):
                logger.error("❌ Failed to index data into vector database")
                return False

        # Verify initialization
        logger.info("\n🔍 Verifying initialization...\n")
        is_populated, collection_counts = self.check_collections_populated()

        if is_populated:
            logger.info("✅ Vector DB initialization successful!")
            logger.info(f"   Collections populated:")
            for name, count in collection_counts.items():
                if count > 0:
                    logger.info(f"   - {name}: {count} documents\n")
            return True
        else:
            logger.error("❌ Vector DB initialization failed - collections still empty")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Initialize vector database with experience data"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinitialization even if data exists",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check status without initializing",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Base data directory path (default: data)",
    )
    parser.add_argument(
        "--chroma-path",
        help="Path to persisted ChromaDB (default: data/embeddings/chroma_db)",
    )
    parser.add_argument(
        "--chroma-host",
        help="ChromaDB server host URL (for remote mode)",
    )

    args = parser.parse_args()

    try:
        # Find data directory (handle running from different locations)
        current_dir = Path.cwd()
        if (current_dir / args.data_dir).exists():
            data_dir = args.data_dir
        elif (current_dir.parent / args.data_dir).exists():
            data_dir = str(current_dir.parent / args.data_dir)
        else:
            logger.error("Error: Could not find data directory")
            sys.exit(1)

        initializer = VectorDBInitializer(
            data_dir=data_dir,
            chroma_path=args.chroma_path,
            chroma_host=args.chroma_host,
        )

        if args.check_only:
            logger.info("=" * 60)
            logger.info("Vector DB Status Check")
            logger.info("=" * 60 + "\n")

            is_populated, collection_counts = initializer.check_collections_populated()
            logger.info(f"Vector DB populated: {is_populated}")
            logger.info(f"Collection counts: {collection_counts}\n")

            has_raw = initializer.check_raw_data_exists()
            structured = initializer.check_structured_data_exists()

            logger.info(f"Raw data available: {has_raw}")
            logger.info(f"Structured data: {structured}\n")

            sys.exit(0 if is_populated else 1)

        # Run initialization
        success = initializer.initialize(force=args.force)
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
