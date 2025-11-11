# GitHub Webhook Auto-Update Setup Guide

## Overview

The auto-updater container listens for GitHub webhook events and automatically pulls the latest code, rebuilds Docker images, and redeploys the application.

## Components

### Webhook Listener
- **Service**: `autoupdater` container
- **Port**: 8008
- **Endpoints**:
  - `POST /github_listener` - Receives GitHub webhook events
  - `GET /github_listener` - Health check (returns script status)
  - `GET /health` - Simple health check

### Deployment Script
- **File**: `auto_update_resnar.sh`
- **Location**: `/auto-updater/auto_update_resnar.sh` (in container)
- **Tasks**:
  1. Pulls latest code from `origin/main`
  2. Builds all Docker images
  3. Restarts containers with `docker compose up -d --build`
  4. Logs all activity with timestamps

## Setup Instructions

### Step 1: Get Your Server's Webhook URL

Determine your server's public URL. Examples:
- `http://your-server.com:8008/github_listener`
- `http://192.168.1.100:8008/github_listener`
- If behind a proxy/reverse proxy, use the proxy URL

**IMPORTANT**: The webhook listener must be publicly accessible from GitHub's servers.

### Step 2: Start the Auto-Updater Container

```bash
cd /path/to/resume-narrator
docker compose up -d autoupdater
```

Verify it's running:
```bash
docker compose logs autoupdater
```

Expected output:
```
autoupdater-1  | 2024-11-10 12:00:00.000000 - INFO - Starting GitHub Webhook Listener...
autoupdater-1  | 2024-11-10 12:00:00.000000 - INFO - Deployment script path: /auto-updater/auto_update_resnar.sh
autoupdater-1  | 2024-11-10 12:00:00.000000 - INFO - Script exists: True
```

### Step 3: Test the Webhook Listener

Test the health endpoint:
```bash
curl -X GET http://localhost:8008/github_listener

# Expected response
{
  "status": "ok",
  "service": "github-webhook-listener",
  "timestamp": "2024-11-10T12:00:00.000000",
  "deploy_script": "/auto-updater/auto_update_resnar.sh",
  "script_exists": true
}
```

Or the simple health check:
```bash
curl -X GET http://localhost:8008/health
```

### Step 4: Configure GitHub Webhook

Go to your GitHub repository:

1. **Navigate to Settings**
   - Click "Settings" on your repository page
   - Select "Webhooks" in the left sidebar

2. **Click "Add webhook"**

3. **Configure the webhook**:
   - **Payload URL**: `http://your-server.com:8008/github_listener`
   - **Content type**: `application/json`
   - **Which events...**: Select "Just the push event" (or "Send me everything")
   - **Active**: ✓ Check the checkbox

4. **Click "Add webhook"**

### Step 5: Test the Webhook

GitHub will automatically test the webhook after creation. You should see:
- A green ✓ checkmark next to the webhook
- A successful POST request in the webhook history

Verify in your container logs:
```bash
docker compose logs -f autoupdater
```

You should see:
```
autoupdater-1  | 2024-11-10 12:15:30.123456 - INFO - GitHub webhook received
autoupdater-1  | 2024-11-10 12:15:30.234567 - INFO - Webhook payload: {...}
autoupdater-1  | 2024-11-10 12:15:30.345678 - INFO - Executing deployment script: /auto-updater/auto_update_resnar.sh
autoupdater-1  | 2024-11-10 12:15:30.456789 - INFO - Deployment script initiated with PID: 12345
```

### Step 6: Monitor Deployment

After pushing to main, check the logs:
```bash
docker compose logs -f autoupdater
```

Expected deployment log:
```
autoupdater-1  | [2024-11-10 12:20:00] === Starting Resume Narrator Auto-Update ===
autoupdater-1  | [2024-11-10 12:20:00] Project directory: /host/project
autoupdater-1  | [2024-11-10 12:20:00] Current branch: main
autoupdater-1  | [2024-11-10 12:20:00] Current commit: 9ac9c5e
autoupdater-1  | [2024-11-10 12:20:01] Starting git pull from origin/main...
autoupdater-1  | [2024-11-10 12:20:02] Successfully pulled latest changes
autoupdater-1  | [2024-11-10 12:20:02] New commit: 2d5b3ee
autoupdater-1  | [2024-11-10 12:20:02] Starting docker compose build and deployment...
autoupdater-1  | [2024-11-10 12:20:45] === Deployment completed successfully ===
```

## Troubleshooting

### Webhook Not Being Triggered

**Check 1: Verify container is running**
```bash
docker compose ps autoupdater
```

Should show `Up` status.

**Check 2: Test the endpoint directly**
```bash
curl -X POST http://localhost:8008/github_listener \
  -H "Content-Type: application/json" \
  -d '{"repository": {"name": "resume-narrator"}}'
```

**Check 3: Check logs**
```bash
docker compose logs -f autoupdater
```

Look for errors like:
- "Deployment script not found"
- "Project directory not found"
- Connection refused errors

### Deployment Fails

Check the full deployment logs:
```bash
docker compose logs autoupdater | tail -100
```

Common issues:
1. **Git pull fails**: Check git credentials, branch name, or SSH keys
2. **Docker build fails**: Check `docker compose up -d --build` works manually
3. **Project path wrong**: Verify `/host/project` matches your actual project location

### GitHub Shows "Failed" for Webhook

1. Go to Webhook settings in GitHub
2. Click the webhook to expand details
3. Check the "Recent Deliveries" tab
4. Click on a failed delivery to see the error response

Common failures:
- **Connection timeout**: Server not accessible from GitHub
- **404 Not Found**: Wrong URL or endpoint
- **500 Internal Server Error**: Script error (check container logs)

## Security Notes

⚠️ **Current Setup**: The webhook listener doesn't validate GitHub signatures. For production:

### Add GitHub Secret Validation (Recommended)

```python
# In webhook_listener.py
import hmac
import hashlib

@app.route('/github_listener', methods=['POST'])
def webhook():
    # Get the signature from GitHub
    signature = request.headers.get('X-Hub-Signature-256', '')

    # Get your webhook secret from GitHub
    secret = os.getenv('GITHUB_WEBHOOK_SECRET')

    # Verify the signature
    if not verify_signature(signature, request.data, secret):
        return {'error': 'Invalid signature'}, 401

    # ... rest of webhook handling
```

### Whitelist GitHub IPs

Get GitHub's IP ranges:
```bash
curl https://api.github.com/meta | jq '.hooks'
```

Configure your firewall to only allow connections from GitHub's servers.

## Files Modified

- `auto-updater/Dockerfile` - Added auto_update_resnar.sh copy and dependencies
- `auto-updater/webhook_listener.py` - Added error handling, logging, health checks
- `auto-updater/auto_update_resnar.sh` - Improved with better logging and error handling
- `GITHUB_WEBHOOK_SETUP.md` - This documentation

## Quick Reference

### Test the webhook endpoint
```bash
curl http://localhost:8008/github_listener
```

### View webhook logs
```bash
docker compose logs -f autoupdater
```

### Manually trigger deployment
```bash
curl -X POST http://localhost:8008/github_listener \
  -H "Content-Type: application/json" \
  -d '{"action": "manual_test"}'
```

### Verify deployment completed
```bash
docker compose ps
```

## Next Steps

1. ✅ Start auto-updater container
2. ✅ Test the webhook listener endpoint
3. ✅ Configure GitHub webhook with correct URL
4. ✅ Test by pushing a small change to main
5. 🔐 (Optional) Add GitHub secret validation for security
6. 🔒 (Optional) Whitelist GitHub IP ranges in firewall
