# GitHub Webhook Auto-Updater Fixes

## Problem

GitHub webhook was being sent successfully, but the auto-updater container was not executing the deployment script. The webhook listener received the event but nothing happened.

## Root Causes Identified & Fixed

### 1. **Missing Deployment Script in Container** ⚠️ (CRITICAL)
**Problem**: The `Dockerfile` was not copying `auto_update_resnar.sh` into the container, but `webhook_listener.py` was trying to execute it at `/app/auto_update_resnar.sh`.

**Fix**: Updated `auto-updater/Dockerfile` to:
```dockerfile
# Copy webhook listener and update script
COPY webhook_listener.py .
COPY auto_update_resnar.sh .

# Make the update script executable
RUN chmod +x auto_update_resnar.sh

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*
```

### 2. **No Error Logging or Visibility**
**Problem**: The original `webhook_listener.py` had no logging, so failures were silent. The webhook would fail but no error would be visible.

**Fix**: Added comprehensive logging to `webhook_listener.py`:
```python
# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log all webhook events
@app.route('/github_listener', methods=['POST', 'GET'])
def webhook():
    logger.info("GitHub webhook received")
    logger.info(f"Webhook payload: {request.json}")

    # Check if deployment script exists (with error logging)
    if not os.path.exists(DEPLOY_SCRIPT):
        logger.error(f"Deployment script not found at: {DEPLOY_SCRIPT}")
        return jsonify({"error": "Deployment script not found", ...}), 500

    logger.info(f"Deployment script initiated with PID: {process.pid}")
```

### 3. **Poor Deployment Script Error Handling**
**Problem**: The `auto_update_resnar.sh` script had minimal error checking and no visibility into what was happening.

**Fix**: Improved `auto_update_resnar.sh` with:
```bash
#!/bin/bash
set -e  # Exit on any error
set -o pipefail  # Exit if any pipeline command fails

# Logging function with timestamps
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Validate prerequisites
log "Project directory: $PROJECT_DIR"
if [ ! -d ".git" ]; then
    log "ERROR: Not a git repository"
    exit 1
fi

# Log progress
log "Current commit: $(git rev-parse --short HEAD)"
log "Starting git pull from origin/main..."

# Better error messages
if ! git pull origin main; then
    log "ERROR: Git pull failed!"
    exit 1
fi

log "Successfully pulled latest changes"
log "New commit: $(git rev-parse --short HEAD)"
```

### 4. **No Health Check Endpoints**
**Problem**: No way to verify the webhook listener was running or working.

**Fix**: Added health check endpoints:
```python
# GET health check
@app.route('/github_listener', methods=['GET'])
def webhook():
    return jsonify({
        "status": "ok",
        "service": "github-webhook-listener",
        "deploy_script": DEPLOY_SCRIPT,
        "script_exists": os.path.exists(DEPLOY_SCRIPT)
    }), 200

# Simple health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "github-webhook-listener",
        "timestamp": datetime.now().isoformat()
    }), 200
```

## Files Modified

### `auto-updater/Dockerfile`
- ✅ Copy `auto_update_resnar.sh` into container
- ✅ Make script executable (`chmod +x`)
- ✅ Install system dependencies: `git`, `docker.io`
- ✅ Cleaner multi-line build instructions

### `auto-updater/webhook_listener.py`
- ✅ Add structured logging with timestamps
- ✅ Add error handling with detailed error messages
- ✅ Support GET requests for health checks
- ✅ Verify deployment script exists before execution
- ✅ Return detailed JSON responses for debugging
- ✅ Log webhook payloads for troubleshooting
- ✅ Better exception handling with traceback logging

### `auto-updater/auto_update_resnar.sh`
- ✅ Add timestamps to all log messages
- ✅ Validate project directory exists
- ✅ Validate git repository
- ✅ Configure git merge strategy
- ✅ Display current/new commit hashes
- ✅ Show container status after deployment
- ✅ Better error messages with context

### New: `GITHUB_WEBHOOK_SETUP.md`
- ✅ Complete setup instructions
- ✅ Step-by-step GitHub webhook configuration
- ✅ Endpoint testing and verification
- ✅ Comprehensive troubleshooting guide
- ✅ Security recommendations
- ✅ Example log output for reference

## How to Verify the Fix

### 1. Rebuild Auto-Updater Container
```bash
cd /path/to/resume-narrator
docker compose up -d --build autoupdater
```

### 2. Check Logs
```bash
docker compose logs autoupdater
```

Expected output:
```
autoupdater-1  | 2024-11-10 12:00:00.000000 - INFO - Starting GitHub Webhook Listener...
autoupdater-1  | 2024-11-10 12:00:00.000000 - INFO - Deployment script path: /auto-updater/auto_update_resnar.sh
autoupdater-1  | 2024-11-10 12:00:00.000000 - INFO - Script exists: True
```

### 3. Test Health Endpoint
```bash
curl -X GET http://localhost:8008/github_listener
```

Expected response:
```json
{
  "status": "ok",
  "service": "github-webhook-listener",
  "deploy_script": "/auto-updater/auto_update_resnar.sh",
  "script_exists": true,
  "timestamp": "2024-11-10T12:00:00.000000"
}
```

### 4. Test Manual Webhook Trigger
```bash
curl -X POST http://localhost:8008/github_listener \
  -H "Content-Type: application/json" \
  -d '{"repository": {"name": "resume-narrator"}, "action": "test"}'
```

Expected response:
```json
{
  "status": "deployment_initiated",
  "message": "Deployment script has been started",
  "pid": 12345,
  "script": "/auto-updater/auto_update_resnar.sh"
}
```

Check logs:
```bash
docker compose logs autoupdater | tail -50
```

Expected output:
```
autoupdater-1  | 2024-11-10 12:15:30.123456 - INFO - GitHub webhook received
autoupdater-1  | 2024-11-10 12:15:30.234567 - INFO - Webhook payload: {...}
autoupdater-1  | 2024-11-10 12:15:30.345678 - INFO - Executing deployment script: /auto-updater/auto_update_resnar.sh
autoupdater-1  | 2024-11-10 12:15:30.456789 - INFO - Deployment script initiated with PID: 12345

# From the deployment script output
autoupdater-1  | [2024-11-10 12:15:31] === Starting Resume Narrator Auto-Update ===
autoupdater-1  | [2024-11-10 12:15:31] Project directory: /host/project
autoupdater-1  | [2024-11-10 12:15:31] Current branch: main
autoupdater-1  | [2024-11-10 12:15:31] Current commit: 2d5b3ee
autoupdater-1  | [2024-11-10 12:15:32] Starting git pull from origin/main...
autoupdater-1  | [2024-11-10 12:15:33] Successfully pulled latest changes
autoupdater-1  | [2024-11-10 12:15:33] New commit: 5471bd6
autoupdater-1  | [2024-11-10 12:15:35] Starting docker compose build and deployment...
autoupdater-1  | [2024-11-10 12:16:00] === Deployment completed successfully ===
```

## GitHub Webhook Configuration

See **[GITHUB_WEBHOOK_SETUP.md](GITHUB_WEBHOOK_SETUP.md)** for complete setup instructions.

Quick summary:
1. Go to GitHub repository Settings → Webhooks
2. Add webhook with:
   - **Payload URL**: `http://your-server.com:8008/github_listener`
   - **Content type**: `application/json`
   - **Events**: "Just the push event" (or all events)
   - **Active**: ✓
3. Test by viewing Recent Deliveries

## Troubleshooting

### Deployment Script Not Found
```
ERROR: Deployment script not found at: /auto-updater/auto_update_resnar.sh
```

**Fix**: Rebuild container with `docker compose up -d --build autoupdater`

### Git Pull Failed
```
[2024-11-10 12:15:33] ERROR: Git pull failed!
```

**Check**:
1. Git credentials configured
2. Branch name is correct (should be `main`)
3. SSH keys mounted correctly
4. Test manually: `docker exec autoupdater-1 bash /auto-updater/auto_update_resnar.sh`

### Docker Compose Not Found
```
[2024-11-10 12:15:35] ERROR: Docker compose up failed!
```

**Check**:
1. Docker socket is mounted: `/var/run/docker.sock:/var/run/docker.sock` ✓
2. Docker binary is available in container
3. Project directory is accessible

## Commit

**Commit**: `5471bd6` - Fix GitHub webhook auto-updater: improve error handling and logging

Changes:
- 4 files changed
- 424 insertions
- 24 deletions

## Quick Start

```bash
# 1. Rebuild the container
docker compose up -d --build autoupdater

# 2. Verify it's running
docker compose logs autoupdater

# 3. Test the endpoint
curl http://localhost:8008/github_listener

# 4. View logs in real-time
docker compose logs -f autoupdater

# 5. Push changes to main branch
git push origin main

# 6. Watch the deployment happen in logs
docker compose logs -f
```
