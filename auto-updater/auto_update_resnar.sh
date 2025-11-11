#!/bin/bash

# Set error handling
set -e
set -o pipefail

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "=== Starting Resume Narrator Auto-Update ==="

# Navigate to the root directory of your project
PROJECT_DIR="/host/project"
if [ ! -d "$PROJECT_DIR" ]; then
    log "ERROR: Project directory not found at $PROJECT_DIR"
    exit 1
fi

log "Project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    log "ERROR: Not a git repository at $PROJECT_DIR"
    exit 1
fi

log "Current branch: $(git rev-parse --abbrev-ref HEAD)"
log "Current commit: $(git rev-parse --short HEAD)"

# Configure git (in case it's needed)
git config pull.rebase false 2>/dev/null || true

log "Starting git pull from origin/main..."
if ! git pull origin main; then
    log "ERROR: Git pull failed!"
    exit 1
fi

log "Successfully pulled latest changes"
log "New commit: $(git rev-parse --short HEAD)"

log "Starting docker compose build and deployment..."
if ! docker compose up -d --build; then
    log "ERROR: Docker compose up failed!"
    exit 1
fi

log "=== Deployment completed successfully ==="
log "Container status:"
docker compose ps

exit 0
