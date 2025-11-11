#!/usr/bin/env python3
"""
Script to populate experience data from raw sources using langextract with Ollama

Reads from:
- data/raw/Profile.csv - LinkedIn profile export
- data/raw/Thornton Resume 2025.8.pdf - PDF resume

Uses LangExtract with Ollama to parse and structure the data into:
- data/experience/work_history.json
- data/experience/skills.json
- data/experience/projects.json
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
import sys
import logging

try:
    import langextract as lx

    HAS_LANGEXTRACT = True
except ImportError:
    HAS_LANGEXTRACT = False

# Try to import PDF libraries
try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LangExtractDocumentParser:
    """Use LangExtract with Ollama to parse and structure experience documents"""

    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.1:8b-instruct-q4_K_M",
        timeout: int = 300,
    ):
        if not HAS_LANGEXTRACT:
            raise ImportError(
                "langextract library required. Install with: pip install langextract"
            )

        self.ollama_host = ollama_host
        self.model = model
        self.timeout = timeout

    def parse_work_history(self, resume_text: str) -> List[Dict[str, Any]]:
        """Parse work history from resume text using LangExtract"""
        logger.info("  Parsing work history with LangExtract...")

        # Define extraction schema with examples
        description = """Extract work history entries from the resume.
        Each entry should contain company name, job title, duration, description of the role,
        key achievements, and relevant skills used."""

        examples = [
            {
                "company": "Tech Corp",
                "title": "Senior Engineer",
                "duration": "Jan 2020 - Dec 2021",
                "description": "Led development of cloud infrastructure",
                "achievements": [
                    "Reduced deployment time by 50%",
                    "Mentored 5 junior engineers",
                ],
                "skills": ["Python", "Kubernetes", "AWS"],
            }
        ]

        try:
            result = lx.extract(
                text_or_documents=resume_text,
                prompt_description=description,
                examples=examples,
                model_id=self.model,
                model_url=self.ollama_host,
                output_format="json_list",
                provider_kwargs={"timeout": self.timeout},
            )
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"    ⚠ Error parsing work history: {e}")
            return []

    def parse_skills(
        self, resume_text: str, profile_text: str = ""
    ) -> List[Dict[str, Any]]:
        """Parse skills from resume using LangExtract"""
        logger.info("  Parsing skills with LangExtract...")

        combined_text = resume_text + "\n" + profile_text

        description = """Extract technical and domain skills from the text.
        Focus on programming languages, frameworks, tools, cloud platforms,
        and domain expertise areas. Include proficiency level and category."""

        examples = [
            {
                "name": "Python",
                "proficiency": "Expert",
                "category": "Programming Languages",
            },
            {
                "name": "Kubernetes",
                "proficiency": "Advanced",
                "category": "Tools",
            },
        ]

        try:
            result = lx.extract(
                text_or_documents=combined_text,
                prompt_description=description,
                examples=examples,
                model_id=self.model,
                model_url=self.ollama_host,
                output_format="json_list",
                provider_kwargs={"timeout": self.timeout},
            )
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"    ⚠ Error parsing skills: {e}")
            return []

    def parse_projects(self, resume_text: str) -> List[Dict[str, Any]]:
        """Parse notable projects from resume using LangExtract"""
        logger.info("  Parsing projects with LangExtract...")

        description = """Extract notable projects from the resume.
        For each project, include the project name, description of what was built,
        technologies/tools used, your role, duration, and key achievements."""

        examples = [
            {
                "name": "AI Chatbot Platform",
                "description": "Built a conversational AI platform",
                "technologies": ["Python", "LLM", "FastAPI"],
                "role": "Lead Developer",
                "duration": "6 months",
                "achievements": [
                    "Reduced query latency by 40%",
                    "Deployed to production with 99.9% uptime",
                ],
            }
        ]

        try:
            result = lx.extract(
                text_or_documents=resume_text,
                prompt_description=description,
                examples=examples,
                model_id=self.model,
                model_url=self.ollama_host,
                output_format="json_list",
                provider_kwargs={"timeout": self.timeout},
            )
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"    ⚠ Error parsing projects: {e}")
            return []


class ExperienceDataPopulator:
    """Extract and populate experience data from raw sources"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.experience_dir = self.data_dir / "experience"

        # Ensure directories exist
        self.experience_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LangExtract parser
        try:
            self.parser = LangExtractDocumentParser()
            self.has_parser = True
        except (ImportError, ConnectionError) as e:
            logger.warning(f"Warning: {e}")
            logger.warning("Will use fallback data generation\n")
            self.has_parser = False

    def load_csv_profile(self) -> Dict[str, Any]:
        """Load profile data from CSV"""
        csv_file = self.raw_dir / "Profile.csv"

        if not csv_file.exists():
            logger.warning(f"Warning: {csv_file} not found")
            return {}

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    return {}

                # Use the first row
                return rows[0]
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return {}

    def extract_pdf_text(self) -> str:
        """Extract text from PDF resume"""
        pdf_file = next(self.raw_dir.glob("*.pdf"), None)

        if not pdf_file:
            logger.warning("Warning: No PDF file found in data/raw/")
            return ""

        # Try pdfplumber first (better for structured extraction)
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            except Exception as e:
                logger.error(f"Error extracting PDF with pdfplumber: {e}")

        # Fall back to PyPDF2
        if HAS_PYPDF2:
            try:
                with open(pdf_file, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    return text
            except Exception as e:
                logger.error(f"Error extracting PDF with PyPDF2: {e}")

        logger.warning(
            "Warning: No PDF extraction library available. "
            "Install pdfplumber or PyPDF2"
        )
        return ""

    def save_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        output_file = self.experience_dir / filename

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"✓ Created {output_file}")

    def populate(self) -> None:
        """Run the full population process"""
        logger.info("Populating experience data...\n")

        # Verify parser is available
        if not self.has_parser:
            raise RuntimeError(
                "LangExtract parser is required to populate experience data. "
                "Please ensure Ollama is running: docker compose up -d ollama"
            )

        # Load profile from CSV
        logger.info("1. Reading profile from CSV...")
        profile = self.load_csv_profile()
        if profile:
            logger.info(
                f"   ✓ Loaded profile for {profile.get('First Name', 'Unknown')}"
            )
        else:
            logger.warning("   ⚠ No profile data found")

        # Extract PDF
        logger.info("\n2. Extracting PDF resume...")
        pdf_text = self.extract_pdf_text()
        if not pdf_text:
            raise RuntimeError(
                "Could not extract PDF text from resume. "
                "Please ensure a PDF file exists in data/raw/ and "
                "pdfplumber or PyPDF2 are installed: pip install pdfplumber PyPDF2"
            )
        logger.info(f"   ✓ Extracted {len(pdf_text)} characters from PDF")

        # Create work history
        logger.info("\n3. Creating work history...")
        work_history = self.parser.parse_work_history(pdf_text)
        if not work_history:
            raise RuntimeError(
                "LangExtract failed to parse work history from resume. "
                "This typically means the model encountered a parsing error. "
                "Please check Ollama logs: docker compose logs ollama"
            )
        self.save_json("work_history.json", {"work_history": work_history})

        # Create skills
        logger.info("\n4. Creating skills list...")
        profile_text = f"{profile.get('Summary', '')} {profile.get('Headline', '')}"
        skills = self.parser.parse_skills(pdf_text, profile_text)
        if not skills:
            raise RuntimeError(
                "LangExtract failed to parse skills from resume. "
                "This typically means the model encountered a parsing error. "
                "Please check Ollama logs: docker compose logs ollama"
            )
        self.save_json("skills.json", {"skills": skills})

        # Create projects
        logger.info("\n5. Creating projects...")
        projects = self.parser.parse_projects(pdf_text)
        if not projects:
            raise RuntimeError(
                "LangExtract failed to parse projects from resume. "
                "This typically means the model encountered a parsing error. "
                "Please check Ollama logs: docker compose logs ollama"
            )
        self.save_json("projects.json", {"projects": projects})

        logger.info("\n✅ Experience data population complete!")
        logger.info("\nNext steps:")
        logger.info("1. Review the generated JSON files in data/experience/")
        logger.info("2. Customize them if needed")
        logger.info(
            "3. Run: python data/load_experience_to_vector_db.py to index the data in ChromaDB"
        )


def main():
    """Main entry point"""
    try:
        # Find data directory (handle running from different locations)
        current_dir = Path.cwd()
        if (current_dir / "data").exists():
            data_dir = "data"
        elif (current_dir.parent / "data").exists():
            data_dir = current_dir.parent / "data"
        else:
            logger.error("Error: Could not find data directory")
            sys.exit(1)

        populator = ExperienceDataPopulator(data_dir)
        populator.populate()

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
