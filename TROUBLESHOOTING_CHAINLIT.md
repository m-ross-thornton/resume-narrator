# Chainlit/Agent UI Troubleshooting Guide

## Issue: Cannot access Chainlit UI on localhost:8080

### Quick Diagnostics

Run these commands on your Mint Linux VM to diagnose the issue:

#### 1. Check if agent container is running
```bash
docker compose ps agent
# Should show: UP
```

#### 2. Check agent container logs
```bash
docker compose logs agent -n 50
# Look for any error messages or "Listening on" messages
```

#### 3. Verify port binding inside container
```bash
docker compose exec agent netstat -tlnp | grep 8080
# Should show: tcp 0 0 0.0.0.0:8080 0.0.0.0:* LISTEN
```

#### 4. Test connectivity from VM host
```bash
# From the VM (not inside container)
curl -I http://localhost:8080
curl -I http://127.0.0.1:8080

# If that doesn't work, try the VM's IP (replace with actual IP)
curl -I http://<VM-IP>:8080
```

#### 5. Check VM firewall (if Mint Linux)
```bash
# Check if firewall is enabled
sudo ufw status

# If enabled, check if 8080 is allowed
sudo ufw allow 8080

# Or disable firewall for testing (not recommended for production)
sudo ufw disable
```

#### 6. Check Docker networking
```bash
# List Docker networks
docker network ls

# Inspect the resnar network
docker network inspect resnar_default
```

---

## Common Issues and Solutions

### Issue 1: "Connection refused" or "Cannot reach server"

**Likely Causes:**
- Container not running or crashed
- Port not exposed in docker-compose.yml
- Firewall blocking port 8080

**Solutions:**
```bash
# 1. Ensure container is running
docker compose up -d agent

# 2. Check logs for startup errors
docker compose logs agent

# 3. Verify port in docker-compose.yml
grep -A 5 "agent:" docker-compose.yml | grep -A 2 ports

# 4. Allow port through firewall
sudo ufw allow 8080/tcp

# 5. Restart Docker daemon
sudo systemctl restart docker
```

### Issue 2: "Container crashes immediately"

**Likely Causes:**
- Missing dependencies
- PromptTemplate validation error (we fixed this with input_variables)
- Environment variables not set correctly
- MCP servers not ready

**Solutions:**
```bash
# Check full logs
docker compose logs agent --tail 200

# Rebuild container (in case of stale cache)
docker compose build --no-cache agent

# Ensure dependencies are installed
docker compose exec agent pip list | grep -E "chainlit|langchain"

# Check if MCP servers are running
docker compose ps mcp-servers
```

### Issue 3: "Address already in use"

**Likely Cause:**
- Another service using port 8080

**Solution:**
```bash
# Find what's using port 8080
sudo lsof -i :8080
# or
sudo netstat -tlnp | grep 8080

# Kill the process or use a different port
# To use a different port, edit docker-compose.yml:
# Change: - "8080:8080"
# To:     - "8081:8080"
```

### Issue 4: Chainlit loads but shows errors about MCP connections

**Likely Cause:**
- MCP servers not running or network connectivity issue

**Solutions:**
```bash
# Check if MCP servers are running
docker compose ps mcp-servers

# Restart MCP servers
docker compose restart mcp-servers

# Check MCP server logs
docker compose logs mcp-servers -n 50

# Verify environment variables in agent container
docker compose exec agent env | grep MCP
```

---

## Access from Different Machines

### From the VM Host (Proxmox host)
You'll need the VM's IP address:
```bash
# Get VM IP from inside the VM
hostname -I

# Then from Proxmox host
curl http://<VM-IP>:8080
```

### From External Machines (e.g., your laptop)
You need the Proxmox host's IP:
```bash
# Access via: http://<PROXMOX-IP>:8080
# You may need to forward the port through Proxmox
```

---

## Docker Compose Useful Commands

```bash
# Start all services
docker compose up -d

# Start only the agent
docker compose up -d agent

# View logs in real-time
docker compose logs -f agent

# Execute commands in container
docker compose exec agent bash

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v

# Rebuild specific container
docker compose build --no-cache agent
```

---

## Chainlit Specific Checks

```bash
# Check if Chainlit is installed
docker compose exec agent pip show chainlit

# Test Chainlit directly
docker compose exec agent chainlit hello

# Check Chainlit version
docker compose exec agent chainlit --version
```

---

## Network Debugging

```bash
# Check if services can communicate
docker compose exec agent ping mcp-servers
docker compose exec agent ping ollama
docker compose exec agent ping chromadb

# Test service connectivity
docker compose exec agent curl http://mcp-servers:9001
docker compose exec agent curl http://ollama:11434/api/tags
docker compose exec agent curl http://chromadb:8000/api/v2/heartbeat
```

---

## Chainlit Configuration

The Dockerfile.agent runs:
```bash
chainlit run agent/ui/chainlit_app.py --host 0.0.0.0 --port 8080
```

This should:
- Listen on all interfaces (0.0.0.0)
- Use port 8080
- Load the chainlit_app.py file

If you need to debug the startup, you can override the CMD:
```bash
docker compose exec agent bash
# Then run manually:
chainlit run agent/ui/chainlit_app.py --host 0.0.0.0 --port 8080 --debug
```

---

## Last Resort: Full Reset

If everything else fails:

```bash
# Stop all services
docker compose down

# Remove unused images/containers
docker system prune -a

# Rebuild from scratch
docker compose build --no-cache

# Start fresh
docker compose up -d

# Monitor logs
docker compose logs -f agent
```

---

## Getting More Help

If the above steps don't work, gather this information:

1. Output of `docker compose ps`
2. Output of `docker compose logs agent` (last 100 lines)
3. Output of `ufw status` (firewall status)
4. Output of `docker network inspect resnar_default`
5. What exact error do you see when trying to access it?
   - Is the page blank?
   - Connection refused?
   - Timeout?
   - Error message?
