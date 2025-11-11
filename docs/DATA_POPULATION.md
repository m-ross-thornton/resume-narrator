# Experience Data Population Guide

This guide explains how to populate experience data from raw sources (CSV, PDF) into the experience JSON files used for ChromaDB vector indexing.

## Overview

The project uses a three-file structure for experience data:

| File | Purpose | Used By |
|------|---------|---------|
| `data/experience/work_history.json` | Professional work experience | Vector DB for searching past roles |
| `data/experience/skills.json` | Technical and domain skills | Vector DB for skill matching |
| `data/experience/projects.json` | Notable projects | Vector DB for project searching |

## Raw Data Sources

Place your raw data in `data/raw/`:

- **Profile.csv** - LinkedIn profile export (CSV format)
- **Resume PDF** - Any PDF resume file (e.g., "Thornton Resume 2025.8.pdf")

## Running the Population Script

```bash
# From project root
python scripts/populate_experience_data.py
```

The script will:
1. ✓ Read your CSV profile
2. ✓ Extract text from PDF (if libraries available)
3. ✓ Generate work_history.json
4. ✓ Generate skills.json
5. ✓ Generate/preserve projects.json

## Customization

After running the script, edit the generated JSON files to add your actual data:

### work_history.json
```json
{
  "work_history": [
    {
      "company": "Company Name",
      "title": "Your Job Title",
      "duration": "X years",
      "description": "Overview of role",
      "achievements": ["Achievement 1", "Achievement 2"],
      "skills": ["Skill 1", "Skill 2"]
    }
  ]
}
```

### skills.json
```json
{
  "skills": [
    {
      "name": "Skill Name",
      "proficiency": "Expert|Advanced|Intermediate|Beginner",
      "category": "Category (e.g., AI/ML, Languages, Tools)"
    }
  ]
}
```

### projects.json
```json
{
  "projects": [
    {
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["Tech 1", "Tech 2"],
      "role": "Your role",
      "duration": "Duration",
      "achievements": ["Achievement 1"]
    }
  ]
}
```

## Indexing in ChromaDB

After populating the JSON files, you need to index them in ChromaDB:

```bash
# Start the vector DB server (will automatically index the files)
docker compose up -d mcp-vector

# The agent can now search through your experience data
docker compose up -d agent
```

## Optional: PDF Text Extraction

For better PDF extraction, install optional libraries:

```bash
pip install pdfplumber  # Recommended
# or
pip install PyPDF2
```

The script supports both libraries and will use pdfplumber if available.

## File Structure

```
data/
├── raw/
│   ├── Profile.csv                    # LinkedIn export
│   └── Thornton Resume 2025.8.pdf    # PDF resume
└── experience/
    ├── work_history.json              # Generated work experience
    ├── skills.json                    # Generated skills list
    └── projects.json                  # Generated projects
```

## Tips

1. **Keep it organized**: Use consistent formatting in JSON files
2. **Categories matter**: Group skills by category for better searching
3. **Achievements talk**: Focus on measurable outcomes in work history
4. **Technology tags**: Use consistent technology names for better matching
5. **Duration formatting**: Use formats like "6 months", "2 years", "12+ years"

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No PDF found" | Ensure your resume PDF is in `data/raw/` |
| "CSV not found" | Export your LinkedIn profile as CSV to `data/raw/Profile.csv` |
| PDF extraction fails | Install pdfplumber: `pip install pdfplumber` |
| JSON won't parse | Use a JSON validator (jsonlint) to check syntax |

## Integration with Vector Search

Once indexed, your experience data can be searched via:

```bash
# Using the vector search tool
curl -X POST http://localhost:9002/tool/search_experience \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning projects", "top_k": 5}'
```
