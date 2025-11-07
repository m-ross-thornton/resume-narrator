#!/usr/bin/env python3
"""
Script to populate experience data from raw sources using Ollama for parsing

Reads from:
- data/raw/Profile.csv - LinkedIn profile export
- data/raw/Thornton Resume 2025.8.pdf - PDF resume

Uses Ollama to parse and structure the data into:
- data/experience/work_history.json
- data/experience/skills.json
- data/experience/projects.json
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any
import sys
import re

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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


class OllamaDocumentParser:
    """Use Ollama to parse and structure experience documents"""

    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.model = "llama3.1:8b-instruct-q4_K_M"

        if not HAS_REQUESTS:
            raise ImportError(
                "requests library required. Install with: pip install requests"
            )

    def call_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate response"""
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.ConnectionError as e:
            print(f"    ⚠ Could not connect to Ollama: {e}")
            return ""
        except requests.exceptions.HTTPError as e:
            print(f"    ⚠ Ollama API error (likely out of memory): {e}")
            return ""
        except Exception as e:
            print(f"    ⚠ Error calling Ollama: {e}")
            return ""

    def parse_work_history(self, resume_text: str) -> List[Dict[str, Any]]:
        """Parse work history from resume text using Ollama"""
        print("  Parsing work history with Ollama...")

        prompt = f"""Extract work history from this resume text and return ONLY valid JSON.

Resume text:
{resume_text[:2000]}

Return a JSON array of work experience entries with this exact structure:
[
  {{
    "company": "Company Name",
    "title": "Job Title",
    "duration": "Time duration",
    "description": "Brief description of role",
    "achievements": ["Achievement 1", "Achievement 2"],
    "skills": ["Skill1", "Skill2"]
  }}
]

Return ONLY the JSON array, no other text."""

        response = self.call_ollama(prompt)
        return self._parse_json_response(response, [])

    def parse_skills(
        self, resume_text: str, profile_text: str = ""
    ) -> List[Dict[str, Any]]:
        """Parse skills from resume using Ollama"""
        print("  Parsing skills with Ollama...")

        combined_text = (resume_text + "\n" + profile_text)[:2000]

        prompt = f"""Extract technical and domain skills from this text and return ONLY valid JSON.

Text:
{combined_text}

Return a JSON array of skills with this exact structure:
[
  {{
    "name": "Skill Name",
    "proficiency": "Expert|Advanced|Intermediate|Beginner",
    "category": "Category (e.g., AI/ML, Languages, Tools, Cloud)"
  }}
]

Focus on technical skills, programming languages, frameworks, tools, and domain expertise.
Return ONLY the JSON array, no other text."""

        response = self.call_ollama(prompt)
        return self._parse_json_response(response, [])

    def parse_projects(self, resume_text: str) -> List[Dict[str, Any]]:
        """Parse notable projects from resume using Ollama"""
        print("  Parsing projects with Ollama...")

        prompt = f"""Extract notable projects from this resume text and return ONLY valid JSON.

Resume text:
{resume_text[:2000]}

Return a JSON array of projects with this exact structure:
[
  {{
    "name": "Project Name",
    "description": "Brief description",
    "technologies": ["Tech1", "Tech2"],
    "role": "Your role in project",
    "duration": "Project duration",
    "achievements": ["Achievement1", "Achievement2"]
  }}
]

Return ONLY the JSON array, no other text."""

        response = self.call_ollama(prompt)
        return self._parse_json_response(response, [])

    def _parse_json_response(self, response: str, default: Any = None) -> Any:
        """Safely parse JSON response from Ollama"""
        try:
            # Try to find JSON in the response (in case there's extra text)
            json_match = re.search(r"\[[\s\S]*\]|\{[\s\S]*\}", response)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return default if default is not None else []
        except json.JSONDecodeError:
            print(f"    ⚠ Could not parse JSON response: {response[:100]}")
            return default if default is not None else []


class ExperienceDataPopulator:
    """Extract and populate experience data from raw sources"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.experience_dir = self.data_dir / "experience"

        # Ensure directories exist
        self.experience_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Ollama parser
        try:
            self.parser = OllamaDocumentParser()
            self.has_ollama = True
        except (ImportError, ConnectionError) as e:
            print(f"Warning: {e}")
            print("Will use fallback data generation\n")
            self.has_ollama = False

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
            "Warning: No PDF extraction library available. "
            "Install pdfplumber or PyPDF2"
        )
        return ""

    def save_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        output_file = self.experience_dir / filename

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Created {output_file}")

    def populate(self) -> None:
        """Run the full population process"""
        print("Populating experience data...\n")

        # Verify Ollama is available
        if not self.has_ollama:
            raise RuntimeError(
                "Ollama is required to populate experience data. "
                "Please ensure Ollama is running: docker compose up -d ollama"
            )

        # Load profile from CSV
        print("1. Reading profile from CSV...")
        profile = self.load_csv_profile()
        if profile:
            print(f"   ✓ Loaded profile for {profile.get('First Name', 'Unknown')}")
        else:
            print("   ⚠ No profile data found")

        # Extract PDF
        print("\n2. Extracting PDF resume...")
        pdf_text = self.extract_pdf_text()
        if not pdf_text:
            raise RuntimeError(
                "Could not extract PDF text from resume. "
                "Please ensure a PDF file exists in data/raw/ and "
                "pdfplumber or PyPDF2 are installed: pip install pdfplumber PyPDF2"
            )
        print(f"   ✓ Extracted {len(pdf_text)} characters from PDF")

        # Create work history
        print("\n3. Creating work history...")
        work_history = self.parser.parse_work_history(pdf_text)
        if not work_history:
            raise RuntimeError(
                "Ollama failed to parse work history from resume. "
                "This typically means Ollama encountered a memory issue or parsing error. "
                "Please check Ollama logs: docker compose logs ollama"
            )
        self.save_json("work_history.json", {"work_history": work_history})

        # Create skills
        print("\n4. Creating skills list...")
        profile_text = f"{profile.get('Summary', '')} {profile.get('Headline', '')}"
        skills = self.parser.parse_skills(pdf_text, profile_text)
        if not skills:
            raise RuntimeError(
                "Ollama failed to parse skills from resume. "
                "This typically means Ollama encountered a memory issue or parsing error. "
                "Please check Ollama logs: docker compose logs ollama"
            )
        self.save_json("skills.json", {"skills": skills})

        # Create projects
        print("\n5. Creating projects...")
        projects = self.parser.parse_projects(pdf_text)
        if not projects:
            raise RuntimeError(
                "Ollama failed to parse projects from resume. "
                "This typically means Ollama encountered a memory issue or parsing error. "
                "Please check Ollama logs: docker compose logs ollama"
            )
        self.save_json("projects.json", {"projects": projects})

        print("\n✅ Experience data population complete!")
        print("\nNext steps:")
        print("1. Review the generated JSON files in data/experience/")
        print("2. Customize them if needed")
        print(
            "3. Run: docker compose up -d mcp-vector " "to index the data in ChromaDB"
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
