# mcp_servers/resume_pdf_server.py
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import json
import os
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP("resume-pdf-server")


class ResumeRequest(BaseModel):
    """Request model for resume generation"""

    template: str = Field(
        default="professional",
        description="Template style: professional, creative, technical, or executive",
    )
    sections: List[str] = Field(
        default=["contact", "summary", "experience", "education", "skills"],
        description="Sections to include in the resume",
    )
    format_options: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional formatting options"
    )
    output_filename: Optional[str] = Field(
        default=None, description="Custom output filename"
    )


class ResumeData:
    """Load and manage resume data"""

    def __init__(self, data_path: str = "/app/data/resume"):
        self.data_path = Path(data_path)
        self.load_data()

    def load_data(self):
        """Load resume data from JSON files"""
        with open(self.data_path / "resume_data.json", "r") as f:
            self.data = json.load(f)

    def get_section(self, section: str) -> Dict:
        """Get specific section data"""
        return self.data.get(section, {})


class ResumePDFGenerator:
    """Generate PDF resumes with different templates"""

    def __init__(self, output_dir: str = "/app/data/outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom styles for different templates"""
        # Professional template styles
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                textColor=colors.HexColor("#2C3E50"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading1"],
                fontSize=14,
                textColor=colors.HexColor("#34495E"),
                spaceAfter=12,
                spaceBefore=12,
                borderWidth=1,
                borderColor=colors.HexColor("#3498DB"),
                borderPadding=5,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="ExperienceTitle",
                parent=self.styles["Heading2"],
                fontSize=12,
                textColor=colors.HexColor("#2C3E50"),
                bold=True,
                spaceAfter=6,
            )
        )

    def generate_professional(self, data: Dict, sections: List[str]) -> str:
        """Generate professional template resume"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_professional_{timestamp}.pdf"
        filepath = self.output_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        story = []

        # Header/Contact Information
        if "contact" in sections:
            contact = data.get("contact", {})
            story.append(Paragraph(contact.get("name", ""), self.styles["CustomTitle"]))

            contact_info = f"""
            {contact.get('email', '')} | {contact.get('phone', '')} | {contact.get('location', '')}
            {contact.get('linkedin', '')} | {contact.get('github', '')}
            """
            story.append(Paragraph(contact_info, self.styles["Normal"]))
            story.append(Spacer(1, 20))

        # Professional Summary
        if "summary" in sections:
            story.append(
                Paragraph("PROFESSIONAL SUMMARY", self.styles["SectionHeader"])
            )
            summary = data.get("summary", "")
            story.append(Paragraph(summary, self.styles["Normal"]))
            story.append(Spacer(1, 12))

        # Work Experience
        if "experience" in sections:
            story.append(Paragraph("WORK EXPERIENCE", self.styles["SectionHeader"]))
            experiences = data.get("experience", [])

            for exp in experiences:
                # Job title and company
                title_text = (
                    f"<b>{exp['title']}</b> | {exp['company']} | {exp['location']}"
                )
                story.append(Paragraph(title_text, self.styles["ExperienceTitle"]))

                # Duration
                duration = f"{exp['start_date']} - {exp['end_date']}"
                story.append(Paragraph(duration, self.styles["Normal"]))

                # Achievements
                for achievement in exp.get("achievements", []):
                    bullet_text = f"• {achievement}"
                    story.append(Paragraph(bullet_text, self.styles["Normal"]))

                story.append(Spacer(1, 8))

        # Education
        if "education" in sections:
            story.append(Paragraph("EDUCATION", self.styles["SectionHeader"]))
            education = data.get("education", [])

            for edu in education:
                edu_text = (
                    f"<b>{edu['degree']}</b> - {edu['institution']} ({edu['year']})"
                )
                story.append(Paragraph(edu_text, self.styles["Normal"]))
                if edu.get("gpa"):
                    story.append(Paragraph(f"GPA: {edu['gpa']}", self.styles["Normal"]))
                story.append(Spacer(1, 6))

        # Skills
        if "skills" in sections:
            story.append(Paragraph("SKILLS", self.styles["SectionHeader"]))
            skills = data.get("skills", {})

            for category, skill_list in skills.items():
                skill_text = f"<b>{category}:</b> {', '.join(skill_list)}"
                story.append(Paragraph(skill_text, self.styles["Normal"]))
                story.append(Spacer(1, 4))

        # Build PDF
        doc.build(story)
        return str(filepath)

    def generate_technical(self, data: Dict, sections: List[str]) -> str:
        """Generate technical template with focus on skills and projects"""
        # Similar structure but with technical focus
        # Include GitHub stats, tech stack visualization, etc.
        pass

    def generate_creative(self, data: Dict, sections: List[str]) -> str:
        """Generate creative template with visual elements"""
        # More visual design, colors, graphics
        pass


@mcp.tool()
async def generate_resume_pdf(request: ResumeRequest) -> Dict[str, Any]:
    """
    Generate a PDF resume from stored data

    Args:
        request: ResumeRequest with template and section preferences

    Returns:
        Dictionary with file path and generation status
    """
    try:
        # Load resume data
        resume_data = ResumeData()

        # Initialize generator
        generator = ResumePDFGenerator()

        # Generate based on template
        if request.template == "professional":
            filepath = generator.generate_professional(
                resume_data.data, request.sections
            )
        elif request.template == "technical":
            filepath = generator.generate_technical(resume_data.data, request.sections)
        elif request.template == "creative":
            filepath = generator.generate_creative(resume_data.data, request.sections)
        else:
            filepath = generator.generate_professional(
                resume_data.data, request.sections
            )

        return {
            "status": "success",
            "message": f"Resume PDF generated successfully",
            "file_path": filepath,
            "template": request.template,
            "sections_included": request.sections,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate resume: {str(e)}",
            "file_path": None,
        }


@mcp.tool()
async def list_resume_templates() -> Dict[str, Any]:
    """
    List available resume templates with descriptions

    Returns:
        Dictionary of available templates
    """
    templates = {
        "professional": {
            "name": "Professional",
            "description": "Clean, traditional format suitable for most industries",
            "best_for": ["Corporate", "Finance", "Consulting", "Management"],
            "features": ["ATS-friendly", "Traditional layout", "Focus on experience"],
        },
        "technical": {
            "name": "Technical",
            "description": "Developer-focused with emphasis on technical skills",
            "best_for": ["Software Engineering", "Data Science", "DevOps", "IT"],
            "features": ["Skills matrix", "Project highlights", "GitHub integration"],
        },
        "creative": {
            "name": "Creative",
            "description": "Visually appealing with modern design elements",
            "best_for": ["Design", "Marketing", "Media", "Startups"],
            "features": ["Visual elements", "Color schemes", "Infographics"],
        },
        "executive": {
            "name": "Executive",
            "description": "Senior-level format emphasizing leadership and achievements",
            "best_for": ["C-Suite", "Director", "VP", "Senior Management"],
            "features": ["Executive summary", "Board positions", "Key metrics"],
        },
    }

    return {"templates": templates, "default": "professional"}


# Add custom REST routes for HTTP API
from starlette.responses import JSONResponse
from starlette.requests import Request


@mcp.custom_route("/health", ["GET"])
async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse({"status": "ok", "service": "resume-pdf-server"})


@mcp.custom_route("/tool/generate_resume_pdf", ["POST"])
async def generate_resume_pdf_endpoint(request: Request):
    """REST endpoint for generating resume PDF"""
    try:
        data = await request.json()
        resume_request = ResumeRequest(**data)
        result = await generate_resume_pdf(resume_request)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=400)


@mcp.custom_route("/tool/search_experience", ["POST"])
async def search_experience_endpoint(request: Request):
    """REST endpoint placeholder for search_experience"""
    return JSONResponse(
        {"status": "success", "message": "Search experience tool would be called here"}
    )


@mcp.custom_route("/tool/explain_architecture", ["POST"])
async def explain_architecture_endpoint(request: Request):
    """REST endpoint placeholder for explain_architecture"""
    return JSONResponse(
        {
            "status": "success",
            "message": "Explain architecture tool would be called here",
        }
    )


@mcp.custom_route("/tool/analyze_skills", ["POST"])
async def analyze_skills_endpoint(request: Request):
    """REST endpoint placeholder for analyze_skills"""
    return JSONResponse(
        {"status": "success", "message": "Analyze skills tool would be called here"}
    )
