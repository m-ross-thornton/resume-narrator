# Data Pipeline Guide: Raw Documents → Vector Database

## Overview

This guide explains the complete end-to-end pipeline for extracting structured data from raw resume/profile documents and indexing them into ChromaDB for semantic search by the Resume Narrator agent.

The pipeline consists of two main stages:

```
┌─────────────────────┐
│  Raw Documents      │
│ • Resume PDF        │
│ • Profile CSV       │
│ • Project Examples  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Stage 1: Data Extraction (Ollama) │
│  scripts/populate_experience_data.py     │
│                                         │
│ Uses Ollama to extract and structure:   │
│ • Work history entries                  │
│ • Skills (technical & domain)           │
│ • Notable projects                      │
└──────────┬──────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Structured JSON Data        │
│ /data/experience/            │
│ • work_history.json          │
│ • skills.json                │
│ • projects.json              │
└──────────┬───────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Stage 2: Vector Indexing (ChromaDB)    │
│  scripts/load_experience_to_vector_db.py    │
│                                         │
│ Indexes structured data into:           │
│ • Semantic embeddings (all-MiniLM)      │
│ • ChromaDB collections                  │
│ • Searchable with metadata              │
└──────────┬──────────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Vector Database             │
│ /data/embeddings/chroma_db/  │
│                              │
│ Collections:                 │
│ • experience (work history)  │
│ • projects                   │
│ • skills                     │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Agent Queries (MCP Tool)    │
│                              │
│ Agent can now semantically   │
│ search indexed experience    │
└──────────────────────────────┘
```

## Stage 1: Data Extraction with Ollama

### Location
`scripts/populate_experience_data.py`

### What It Does
Reads raw documents (PDF resume and CSV profile) and uses Ollama with Ollama to intelligently extract and structure data into consistent JSON format.

### Key Classes

#### `OllamaDocumentParser`
Main extraction engine using Ollama with few-shot examples.

**Methods:**
- `parse_work_history(resume_text: str) -> List[Dict]`
  - Extracts: company, title, duration, description, achievements, skills
  - Returns list of work history entries

- `parse_skills(resume_text: str, profile_text: str) -> List[Dict]`
  - Extracts: name, proficiency, category
  - Returns list of skill entries

- `parse_projects(resume_text: str) -> List[Dict]`
  - Extracts: name, description, technologies, role, duration, achievements
  - Returns list of project entries

#### `ExperienceDataPopulator`
Orchestrates the full extraction pipeline.

**Methods:**
- `load_csv_profile() -> Dict`
  - Loads LinkedIn profile export from /data/raw/Profile.csv

- `extract_pdf_text() -> str`
  - Extracts text from PDF resume in /data/raw/
  - Tries pdfplumber first, falls back to PyPDF2

- `populate() -> None`
  - Runs complete extraction pipeline
  - Saves results to /data/experience/ as JSON files

### Requirements

```
Ollama>=0.1.0
requests>=2.31.0
pdfplumber>=0.10.0
PyPDF2>=3.17.0
pydantic>=2.0.0
```

Install with:
```bash
pip install -r scripts/requirements.txt
```

### Running Stage 1

```bash
# From project root
python scripts/populate_experience_data.py
```

**What happens:**
1. Finds data directory (works from any location)
2. Loads profile from /data/raw/Profile.csv
3. Extracts text from PDF in /data/raw/
4. Uses Ollama with Ollama to parse:
   - Work history → /data/experience/work_history.json
   - Skills → /data/experience/skills.json
   - Projects → /data/experience/projects.json

**Output:**
```
Populating experience data...

1. Reading profile from CSV...
   ✓ Loaded profile for Michael Thornton

2. Extracting PDF resume...
   ✓ Extracted 12345 characters from PDF

3. Creating work history...
   ✓ Created /Users/ross/Projects/resnar/data/experience/work_history.json

4. Creating skills list...
   ✓ Created /Users/ross/Projects/resnar/data/experience/skills.json

5. Creating projects...
   ✓ Created /Users/ross/Projects/resnar/data/experience/projects.json

✅ Experience data population complete!
```

### Requirements for Stage 1

- **Ollama running:** `docker compose up -d ollama`
- **Model available:** `ollama pull llama3.1:8b-instruct-q4_K_M` (or specified model)
- **Raw files present:**
  - `/data/raw/Profile.csv` (LinkedIn export)
  - `/data/raw/Thornton Resume 2025.8.pdf` (or any PDF in /data/raw/)

### Ollama Features Used

1. **Few-shot examples:** Each extraction method provides example schemas
2. **Structured output:** Enforces consistent JSON format
3. **Ollama integration:** Uses local LLM via Ollama API
4. **Timeout handling:** 300-second timeout for longer documents
5. **Error handling:** Graceful fallback if extraction fails

## Stage 2: Vector Database Indexing

### Location
`scripts/load_experience_to_vector_db.py`

### What It Does
Reads the structured JSON files from Stage 1 and indexes them into ChromaDB with semantic embeddings for fast similarity search.

### Key Functions

#### `load_work_history() -> Tuple[List[str], List[Dict]]`
- Loads /data/experience/work_history.json
- Creates rich documents combining company, title, duration, description, achievements, skills
- Stringifies list fields (skills, achievements) for ChromaDB compatibility
- Returns (documents, metadata) tuples

#### `load_projects() -> Tuple[List[str], List[Dict]]`
- Loads /data/experience/projects.json
- Creates documents from project name, description, technologies
- Returns (documents, metadata) tuples

#### `load_skills() -> Tuple[List[str], List[Dict]]`
- Loads /data/experience/skills.json
- Creates documents from skill categories with proficiency levels
- Returns (documents, metadata) tuples

#### `index_collection(db_manager, collection_name, documents, metadata) -> bool`
- Indexes documents into specified ChromaDB collection
- Returns success status

### Running Stage 2

```bash
# Load all collections (default)
python scripts/load_experience_to_vector_db.py

# Load specific collection
python scripts/load_experience_to_vector_db.py --collections work_history projects

# Reset database before loading
python scripts/load_experience_to_vector_db.py --reset

# Custom ChromaDB path
python scripts/load_experience_to_vector_db.py --chroma-path /custom/path/chroma_db
```

**CLI Options:**
- `--collections` [work_history|projects|skills]: Which collections to load (default: all)
- `--reset`: Clear database before loading
- `--chroma-path`: Path to ChromaDB directory (default: data/embeddings/chroma_db)

### Output

```
2025-11-11 10:30:45,123 - INFO - Starting vector database population...
2025-11-11 10:30:45,124 - INFO - Collections to load: ['work_history', 'projects', 'skills']
2025-11-11 10:30:45,234 - INFO - Connected to ChromaDB at data/embeddings/chroma_db

--- Loading Work History ---
2025-11-11 10:30:45,345 - INFO - Loaded 4 work history entries
2025-11-11 10:30:47,456 - INFO - Successfully indexed 4 documents to 'experience' collection

--- Loading Projects ---
2025-11-11 10:30:47,567 - INFO - Loaded X projects
2025-11-11 10:30:49,678 - INFO - Successfully indexed X documents to 'projects' collection

--- Loading Skills ---
2025-11-11 10:30:49,789 - INFO - Loaded Y skill categories
2025-11-11 10:30:51,890 - INFO - Successfully indexed Y documents to 'skills' collection

==================================================
2025-11-11 10:30:52,001 - INFO - Data loading complete: 3/3 collections loaded
2025-11-11 10:30:52,002 - INFO - ✓ All collections loaded successfully
```

### ChromaDB Considerations

**Metadata constraints:** ChromaDB only accepts strings, ints, floats, and bools in metadata.
- All list fields are stringified with `, `.join()
- Example: `"skills": "Python, Kubernetes, AWS"` instead of `["Python", "Kubernetes", "AWS"]`

**Collections created:**
- **experience**: Work history with company, title, duration, skills
- **projects**: Projects with name, role, duration, technologies
- **skills**: Skills with category, proficiency_level, years_of_experience

## Testing

### Test Suite
Location: `tests/test_vector_db_data_pipeline.py`

**Test Classes:**
- `TestDataLoading`: Validates source JSON files exist and are valid
- `TestVectorDatabaseIndexing`: Verifies indexing works correctly
- `TestVectorDatabaseSearch`: Tests semantic search functionality
- `TestVectorSearchRequest`: Validates search request model
- `TestDataIntegration`: End-to-end pipeline test

**Run tests:**
```bash
pytest tests/test_vector_db_data_pipeline.py -v
```

**All tests passing:** ✓ 15/15

## Complete Workflow Example

```bash
# 1. Ensure Ollama is running
docker compose up -d ollama

# 2. Pull the model if needed
ollama pull llama3.1:8b-instruct-q4_K_M

# 3. Extract data from raw documents
python scripts/populate_experience_data.py

# 4. Index extracted data into vector database
python scripts/load_experience_to_vector_db.py

# 5. Verify indexing with tests
pytest tests/test_vector_db_data_pipeline.py -v

# 6. Agent can now search indexed data via MCP tools
# (Handled by mcp-vector server at runtime)
```

## Agent Integration

The Resume Narrator agent can now search indexed experience data via the `search_experience()` MCP tool:

```python
# Agent query example
result = search_experience(
    query="machine learning projects",
    collection="experience",
    top_k=5
)

# Returns:
# [
#   {
#     "document": "Company: Peraton\nTitle: AI/ML Engineer\n...",
#     "metadata": {"company": "Peraton", "title": "AI/ML Engineer", ...},
#     "similarity": 0.87
#   },
#   ...
# ]
```

## Troubleshooting

### Issue: "Could not connect to Ollama"
**Solution:** Start Ollama service
```bash
docker compose up -d ollama
# or locally: ollama serve
```

### Issue: "Ollama not installed"
**Solution:** Install dependencies
```bash
pip install -r scripts/requirements.txt
```

### Issue: "Could not extract PDF text"
**Solution:** Ensure PDF file exists and libraries are installed
```bash
ls data/raw/*.pdf
pip install pdfplumber PyPDF2
```

### Issue: "Ollama failed to parse"
**Solution:** Check Ollama logs for memory issues
```bash
docker compose logs ollama
```

## Files Summary

| File | Purpose |
|------|---------|
| `scripts/populate_experience_data.py` | Stage 1: Extract raw docs → JSON |
| `scripts/requirements.txt` | Dependencies for extraction scripts |
| `scripts/load_experience_to_vector_db.py` | Stage 2: Index JSON → Vector DB |
| `data/experience/work_history.json` | Structured work history data |
| `data/experience/projects.json` | Structured projects data |
| `data/experience/skills.json` | Structured skills data |
| `data/embeddings/chroma_db/` | ChromaDB persistent storage |
| `tests/test_vector_db_data_pipeline.py` | Test suite (15 tests) |

## Dependencies

### Stage 1 (Extraction)
- **Ollama**: Structured data extraction with LLMs
- **pdfplumber**: PDF text extraction
- **PyPDF2**: PDF backup extraction
- **pydantic**: Data validation
- **requests**: HTTP client (for Ollama)

### Stage 2 (Indexing)
- **chromadb**: Vector database
- **sentence-transformers**: Embedding model (all-MiniLM-L6-v2)
- **numpy**: Numerical operations

### Runtime
- **Ollama**: Local LLM inference (for Stage 1)
- **Docker**: Container orchestration

## Future Enhancements

1. **Raw document support**: Load from project_examples.rtf
2. **Incremental updates**: Only re-extract changed sections
3. **Custom embedding models**: Support other embedding providers
4. **Quality metrics**: Validate extracted data against schema
5. **Web UI**: Interactive data validation and correction
6. **Multi-language support**: Extract from non-English documents
7. **Source tracking**: Link extracted data back to original documents

