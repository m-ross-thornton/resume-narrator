# Vector Database Initialization Guide

## Overview

The vector database initialization system uses a **hybrid approach** to populate ChromaDB with experience data. This design provides:

- **Fast restarts**: Skips initialization if data already exists
- **Decoupled services**: Initialization is optional, not required for vector server startup
- **Manual control**: Can be run independently via CLI or Docker
- **CI/CD friendly**: Supports automated initialization in deployment pipelines

## Architecture

The initialization system consists of three stages:

```
Raw Documents (PDF, CSV)
    ↓
[Stage 1: populate_experience_data.py]
    ↓
Structured JSON Data (work_history.json, projects.json, skills.json)
    ↓
[Stage 2: load_experience_to_vector_db.py]
    ↓
ChromaDB Vector Collections (experience, projects, skills)
```

### Stage 1: Data Population

`scripts/populate_experience_data.py` extracts and structures raw documents using Ollama:

- Reads: `data/raw/Profile.csv` (LinkedIn profile export)
- Reads: `data/raw/Thornton Resume 2025.8.pdf` (resume PDF)
- Uses Ollama to parse documents into structured JSON
- Outputs:
  - `data/experience/work_history.json`
  - `data/experience/skills.json`
  - `data/experience/projects.json`

**Dependencies**: requests, pdfplumber, PyPDF2, Ollama service

### Stage 2: Vector Indexing

`scripts/load_experience_to_vector_db.py` indexes structured data into ChromaDB:

- Reads: JSON files from `data/experience/`
- Converts documents and metadata for embedding
- Creates semantic embeddings using sentence-transformers
- Indexes into ChromaDB collections: experience, projects, skills

**Dependencies**: chromadb, sentence-transformers

### Stage 3: Verification

`scripts/init_vector_db.py` orchestrates the full pipeline and verifies completion:

- Checks if ChromaDB collections are populated
- Runs Stage 1 and 2 as needed
- Verifies data was indexed successfully
- Provides detailed status reporting

## Usage

### 1. Local Development (CLI)

#### Auto-initialize (recommended)
```bash
# Initializes only if vector DB is empty
python scripts/init_vector_db.py
```

#### Force re-initialization
```bash
# Reinitialize even if data exists
python scripts/init_vector_db.py --force
```

#### Check status only
```bash
# See what data exists without initializing
python scripts/init_vector_db.py --check-only
```

#### With custom paths
```bash
# Specify custom ChromaDB location
python scripts/init_vector_db.py --chroma-path /custom/path/chroma_db

# Specify custom data directory
python scripts/init_vector_db.py --data-dir /custom/data
```

### 2. Docker - One-time initialization

```bash
# Run init container once and exit
docker compose --profile init run --rm init-vector-db

# With force flag
docker compose --profile init run --rm init-vector-db \
  python /app/scripts/init_vector_db.py --force
```

### 3. Docker - As part of full stack

```bash
# Start all services (without init)
docker compose up -d

# In another terminal, initialize if needed
docker compose --profile init run --rm init-vector-db

# Or combine: start stack + initialize
docker compose up -d chromadb ollama && \
docker compose --profile init run --rm init-vector-db && \
docker compose up -d mcp-resume mcp-vector mcp-code agent
```

### 4. Docker - Kubernetes-style init container

You can modify docker-compose.yml to use init-vector-db as a startup dependency:

```yaml
mcp-vector:
  depends_on:
    init-vector-db:
      condition: service_completed_successfully
```

This ensures vector server only starts after initialization completes.

### 5. CI/CD Pipeline

```bash
# In your deployment script
#!/bin/bash
set -e

# Start backend services
docker compose up -d chromadb ollama

# Wait for health checks
docker compose exec chromadb curl http://localhost:8000/api/v2/heartbeat
docker compose exec ollama curl http://localhost:11434/api/tags

# Initialize vector DB
docker compose --profile init run --rm init-vector-db

# Start MCP servers
docker compose up -d mcp-resume mcp-vector mcp-code agent
```

## Configuration

### Environment Variables

```bash
# Docker builder image name
DOCKER_USERNAME=yourname  # default: thornton

# ChromaDB configuration (optional)
CHROMA_HOST=http://chromadb:8000  # auto-configured in Docker
CHROMA_PATH=/app/data/embeddings/chroma_db  # default location
```

### Command Line Options

```
usage: init_vector_db.py [-h] [--force] [--check-only]
                         [--data-dir DATA_DIR]
                         [--chroma-path CHROMA_PATH]
                         [--chroma-host CHROMA_HOST]

optional arguments:
  -h, --help                Show help message
  --force                   Force reinitialization even if data exists
  --check-only              Check status without initializing
  --data-dir DATA_DIR       Base data directory path (default: data)
  --chroma-path CHROMA_PATH Path to persisted ChromaDB
  --chroma-host CHROMA_HOST ChromaDB server host URL (remote mode)
```

## How It Works

### Hybrid Initialization Algorithm

```python
def initialize(force=False):
    # 1. Check if vector DB is populated
    is_populated = check_collections()

    # 2. If populated and not forced, skip
    if is_populated and not force:
        return True  # Fast path

    # 3. Check if raw data exists
    has_raw_data = check_raw_files()

    # 4. Check if structured data exists
    structured_data_exists = check_json_files()

    # 5. Run stages as needed
    if needs_stage1:
        run(populate_experience_data.py)

    if needs_stage2:
        run(load_experience_to_vector_db.py)

    # 6. Verify completion
    return verify_collections_populated()
```

### Decision Tree

```
┌─ Is vector DB populated?
│  ├─ Yes + not forced → SKIP (fast restart)
│  └─ No or forced → Continue
│
├─ Does raw data exist?
│  ├─ Yes → Run Stage 1
│  └─ No → Log warning, skip
│
├─ Is structured data missing?
│  ├─ Yes → Run Stage 1
│  └─ No → Continue to Stage 2
│
├─ Is vector DB empty or forced?
│  ├─ Yes → Run Stage 2
│  └─ No → SKIP
│
└─ Verify collections populated → Success/Failure
```

## Status Checking

### View current state
```bash
python scripts/init_vector_db.py --check-only
```

Output example:
```
Vector DB Status: ✓ Populated
  experience: 5 documents
  projects: 3 documents
  skills: 28 documents

Raw data check:
  PDF files: 1 found
  CSV profile: found

Structured data:
  work_history: exists with content
  projects: exists with content
  skills: exists with content
```

### Check specific collections
```bash
# From Python
from mcp_servers.vector_db_server import VectorDBManager

db = VectorDBManager(persist_directory="/app/data/embeddings/chroma_db")
collection = db.client.get_collection("experience")
print(f"Documents in experience: {collection.count()}")
```

### View ChromaDB directly
```bash
# Via Docker
docker compose exec chromadb sqlite3 /chroma/chroma/chroma.db \
  "SELECT COUNT(*) FROM embeddings;"

# Via Python
import chromadb
client = chromadb.PersistentClient(path="/app/data/embeddings/chroma_db")
for col in ["experience", "projects", "skills"]:
    c = client.get_collection(col)
    print(f"{col}: {c.count()}")
```

## Troubleshooting

### Vector DB is not being populated

1. **Check raw data exists**
   ```bash
   ls -la data/raw/
   # Should contain: Profile.csv and at least one PDF
   ```

2. **Verify Ollama service**
   ```bash
   curl http://localhost:11434/api/tags
   # Should return list of available models
   ```

3. **Check initialization logs**
   ```bash
   # For Docker
   docker compose logs init-vector-db

   # For CLI
   python scripts/init_vector_db.py --check-only
   ```

4. **Force re-initialization**
   ```bash
   python scripts/init_vector_db.py --force
   ```

### Collections are empty after initialization

1. **Verify structured JSON files exist**
   ```bash
   ls -la data/experience/
   # Should contain: work_history.json, projects.json, skills.json
   ```

2. **Check JSON validity**
   ```bash
   python -m json.tool data/experience/work_history.json | head -20
   ```

3. **Check ChromaDB is healthy**
   ```bash
   curl http://localhost:8000/api/v2/heartbeat
   ```

4. **View detailed logs**
   ```bash
   python scripts/init_vector_db.py -vv  # Verbose logging
   ```

### Initialization times out

- Stage 1 (populate_experience_data.py) may take 5-10 minutes with Ollama
- Stage 2 (load_experience_to_vector_db.py) typically completes in <1 minute
- Total timeout is set to 10 minutes per stage

If timing out:
1. Check Ollama service performance: `curl http://localhost:11434/api/generate`
2. Verify adequate disk space: `df -h`
3. Increase system resources (CPU, RAM) for Ollama

### Duplicate data in vector DB

```bash
# Reset collections before reinitializing
python scripts/load_experience_to_vector_db.py --reset

# Or force full reinitialization
python scripts/init_vector_db.py --force
```

## Best Practices

1. **Run initialization after setup**
   ```bash
   docker compose up -d chromadb ollama
   docker compose --profile init run --rm init-vector-db
   ```

2. **Check status before querying**
   ```bash
   python scripts/init_vector_db.py --check-only
   # Verify collections have documents before using vector server
   ```

3. **Handle initialization in CI/CD**
   ```bash
   # Always initialize in fresh deployments
   docker compose --profile init run --rm init-vector-db
   ```

4. **Monitor initialization progress**
   ```bash
   # Watch logs in real-time
   docker compose logs -f init-vector-db
   ```

5. **Backup vector DB after initialization**
   ```bash
   # The data is persisted in data/embeddings/chroma_db/
   tar -czf chroma_db_backup.tar.gz data/embeddings/chroma_db/
   ```

## Performance Considerations

### Initialization Time

- **Stage 1 (populate_experience_data.py)**
  - Cold start (pulling model): 5-10 minutes
  - Warm start (model cached): 2-5 minutes
  - Depends on: PDF size, Ollama model size, hardware

- **Stage 2 (load_experience_to_vector_db.py)**
  - Typically: <1 minute
  - Depends on: number of documents, ChromaDB performance

- **Total first run**: 7-15 minutes
- **Subsequent runs (with --force)**: 3-7 minutes

### Optimization Tips

1. **Use GPU acceleration** (if available)
   - Ollama automatically uses CUDA when available
   - Set `runtime: nvidia` in docker-compose.yml

2. **Cache Ollama models**
   - Models persist in `ollama_data` volume
   - Subsequent runs reuse cached models

3. **Adjust ChromaDB settings**
   - Default configuration is optimized for local deployment
   - See [ChromaDB docs](https://docs.trychroma.com/) for tuning

4. **Monitor resource usage**
   ```bash
   docker stats
   # Watch CPU, memory, and disk I/O during initialization
   ```

## Integration Examples

### With Kubernetes

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: vector-db-init
spec:
  template:
    spec:
      initContainers:
      - name: init-vector-db
        image: thornton/resume-narrator-mcp:latest
        command: ["python", "/app/scripts/init_vector_db.py"]
        volumeMounts:
        - name: data
          mountPath: /app/data
      containers:
      - name: vector-server
        image: thornton/resume-narrator-mcp:latest
        command: ["python", "/app/mcp-servers/vector_http_server.py"]
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: resume-data
```

### With Terraform

```hcl
resource "docker_container" "init_vector_db" {
  name  = "init-vector-db"
  image = docker_image.mcp.id

  depends_on = [
    docker_container.chromadb,
    docker_container.ollama
  ]

  mounts {
    type        = "bind"
    source      = "${path.module}/data"
    target      = "/app/data"
  }

  command = ["python", "/app/scripts/init_vector_db.py"]
}
```

## Related Documentation

- [Data Pipeline Guide](./DATA_PIPELINE_GUIDE.md) - Detailed explanation of data extraction and indexing
- [Vector DB Search](./VECTOR_DB_SEARCH.md) - How to query indexed data (if available)
- [Docker Setup](../README.md#docker-setup) - Container configuration

## FAQ

**Q: Do I need to run initialization every time I start the system?**
A: No. The hybrid approach checks if data exists and skips initialization for fast restarts. Use `--force` to reinitialize.

**Q: Can I initialize with custom data?**
A: Yes. Place your files in `data/raw/` (CSV and PDF) and run the initialization script.

**Q: What if initialization fails?**
A: Check the logs for the specific error, address the root cause, and use `--force` to retry.

**Q: Can multiple services initialize simultaneously?**
A: The initialization script is designed for single-run usage. Use `--check-only` to verify before concurrent operations.

**Q: How do I reset and reinitialize everything?**
A: Run `python scripts/init_vector_db.py --force` to completely reinitialize the vector database.
