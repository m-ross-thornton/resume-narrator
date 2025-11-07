#!/usr/bin/env python3
"""
Script to populate experience data from raw sources (CSV, PDF) into experience JSONs

Reads from:
- data/raw/Profile.csv - LinkedIn profile export
- data/raw/Thornton Resume 2025.8.pdf - PDF resume

Writes to:
- data/experience/work_history.json
- data/experience/skills.json
- data/experience/projects.json (if not already populated)
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
import sys

# Try to import PDF libraries
try:
    import PyPDF2

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class ExperienceDataPopulator:
    """Extract and populate experience data from raw sources"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.experience_dir = self.data_dir / "experience"

        # Ensure directories exist
        self.experience_dir.mkdir(parents=True, exist_ok=True)

    def load_csv_profile(self) -> Dict[str, Any]:
        """Load profile data from CSV"""
        csv_file = self.raw_dir / "Profile.csv"

        if not csv_file.exists():
            print(f"Warning: {csv_file} not found")
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
            print(f"Error reading CSV: {e}")
            return {}

    def extract_pdf_text(self) -> str:
        """Extract text from PDF resume"""
        pdf_file = next(self.raw_dir.glob("*.pdf"), None)

        if not pdf_file:
            print("Warning: No PDF file found in data/raw/")
            return ""

        # Try pdfplumber first (better for structured extraction)
        if HAS_PDFPLUMBER:
            try:
                import pdfplumber

                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            except Exception as e:
                print(f"Error extracting PDF with pdfplumber: {e}")

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
                print(f"Error extracting PDF with PyPDF2: {e}")

        print(
            "Warning: No PDF extraction library available. Install pdfplumber or PyPDF2"
        )
        return ""

    def create_work_history(self, profile: Dict) -> List[Dict[str, Any]]:
        """Create work history from profile data"""
        # For now, return a template that users can populate
        work_history = [
            {
                "company": "Department of Defense (DoD)",
                "title": "Senior AI/ML Engineer and Data Scientist",
                "duration": "12+ years",
                "description": profile.get("Summary", ""),
                "achievements": [
                    "Architected and deployed Generative AI solutions",
                    "Integrated RAG, Azure OpenAI, and LangChain with enterprise platforms",
                    "Delivered mission-critical solutions within DoD sector",
                ],
                "skills": [
                    "AI/ML",
                    "Data Science",
                    "Generative AI",
                    "Azure OpenAI",
                    "LangChain",
                    "Palantir",
                    "Python",
                ],
            }
        ]

        return work_history

    def create_skills(self, profile: Dict) -> List[Dict[str, Any]]:
        """Create skills list from profile"""
        # Extract from summary and other fields
        default_skills = [
            {
                "name": "Generative AI",
                "proficiency": "Expert",
                "category": "AI/ML",
            },
            {"name": "Python", "proficiency": "Expert", "category": "Languages"},
            {"name": "Data Science", "proficiency": "Expert", "category": "Data"},
            {
                "name": "Azure OpenAI",
                "proficiency": "Advanced",
                "category": "Cloud/AI",
            },
            {"name": "LangChain", "proficiency": "Advanced", "category": "Frameworks"},
            {"name": "Palantir", "proficiency": "Advanced", "category": "Tools"},
            {
                "name": "Microsoft Power Platform",
                "proficiency": "Advanced",
                "category": "Enterprise",
            },
            {"name": "SharePoint", "proficiency": "Advanced", "category": "Enterprise"},
            {
                "name": "Data Pipelines",
                "proficiency": "Advanced",
                "category": "Data",
            },
            {"name": "SQL", "proficiency": "Advanced", "category": "Databases"},
        ]

        return default_skills

    def create_projects(self) -> List[Dict[str, Any]]:
        """Create projects list - users should customize this"""
        # Return projects from existing file if it has data, otherwise use template
        projects_file = self.experience_dir / "projects.json"

        if projects_file.exists():
            try:
                with open(projects_file, "r") as f:
                    data = json.load(f)
                    return data.get("projects", [])
            except Exception:
                pass

        # Return default template
        return [
            {
                "name": "E-Commerce Platform Modernization",
                "description": "Led migration of legacy monolith to microservices",
                "technologies": ["Python", "FastAPI", "Kubernetes", "PostgreSQL"],
                "role": "Lead Developer",
                "duration": "6 months",
                "achievements": [
                    "Reduced latency by 40%",
                    "Improved deployment frequency from monthly to daily",
                    "Implemented CI/CD pipeline",
                ],
            }
        ]

    def save_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        output_file = self.experience_dir / filename

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Created {output_file}")

    def populate(self) -> None:
        """Run the full population process"""
        print("Populating experience data...\n")

        # Load profile from CSV
        print("1. Reading profile from CSV...")
        profile = self.load_csv_profile()
        if profile:
            print(f"   ✓ Loaded profile for {profile.get('First Name', 'Unknown')}")
        else:
            print("   ⚠ No profile data found")

        # Extract PDF (optional for later use)
        print("\n2. Extracting PDF resume...")
        pdf_text = self.extract_pdf_text()
        if pdf_text:
            print(f"   ✓ Extracted {len(pdf_text)} characters from PDF")
        else:
            print("   ⚠ Could not extract PDF text")

        # Create work history
        print("\n3. Creating work history...")
        work_history = self.create_work_history(profile)
        self.save_json("work_history.json", {"work_history": work_history})

        # Create skills
        print("\n4. Creating skills list...")
        skills = self.create_skills(profile)
        self.save_json("skills.json", {"skills": skills})

        # Create/preserve projects
        print("\n5. Handling projects...")
        projects = self.create_projects()
        self.save_json("projects.json", {"projects": projects})

        print("\n✅ Experience data population complete!")
        print("\nNext steps:")
        print("1. Review the generated JSON files in data/experience/")
        print("2. Customize work_history.json with your actual work experience")
        print("3. Customize projects.json with your actual projects")
        print("4. Run: docker compose up mcp-vector to index the data in ChromaDB")


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
            print("Error: Could not find data directory")
            sys.exit(1)

        populator = ExperienceDataPopulator(data_dir)
        populator.populate()

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
