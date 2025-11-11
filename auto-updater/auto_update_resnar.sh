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
PROJECT_DIR="${PROJECT_DIR:-/host/project}"
if [ ! -d "$PROJECT_DIR" ]; then
    log "ERROR: Project directory not found at $PROJECT_DIR"
    log "Available directories:"
    ls -la /host/ 2>/dev/null || log "  /host directory not found"
    exit 1
fi

log "Project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    log "ERROR: Not a git repository at $PROJECT_DIR"
    log "Current directory contents:"
    ls -la
    exit 1
fi

# CRITICAL: Configure git to trust this directory
# This prevents "dubious ownership" errors when container user differs from repo owner
log "Configuring git to trust repository..."
git config --global --add safe.directory "$PROJECT_DIR" 2>/dev/null || true

log "Current branch: $(git rev-parse --abbrev-ref HEAD)"
log "Current commit: $(git rev-parse --short HEAD)"

# Configure git
log "Configuring git..."
git config pull.rebase false 2>/dev/null || true
git config user.email "auto-updater@resume-narrator.local" 2>/dev/null || true
git config user.name "Resume Narrator Auto-Updater" 2>/dev/null || true

# Check for uncommitted changes
log "Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    log "WARNING: Found uncommitted changes, stashing them..."
    git stash || log "ERROR: Failed to stash changes"
fi

# Check git status
log "Git status:"
git status

log "Starting git pull from origin/main..."
if ! git pull origin main 2>&1; then
    log "ERROR: Git pull failed!"
    log "Git fetch output:"
    git fetch origin 2>&1 || true
    log "Attempting to reset to origin/main..."
    git reset --hard origin/main || log "ERROR: Failed to reset to origin/main"
    exit 1
fi

log "Successfully pulled latest changes"
log "New commit: $(git rev-parse --short HEAD)"

# Check if docker is accessible
log "Checking docker daemon..."
if ! docker ps > /dev/null 2>&1; then
    log "ERROR: Docker daemon not accessible!"
    exit 1
fi

log "Docker is accessible, proceeding with build and deployment..."

log "Starting docker compose build and deployment..."
if ! docker compose up -d --build 2>&1; then
    log "ERROR: Docker compose up failed!"
    log "Docker compose ps output:"
    docker compose ps 2>&1 || true
    exit 1
fi

log "=== Deployment completed successfully ==="
log "Container status:"
docker compose ps

log "Waiting for services to become healthy..."
sleep 10

log "Final container status:"
docker compose ps

exit 0
