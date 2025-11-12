# MCP Servers - Docker Setup

## Quick Start

### Option 1: Run Both Servers with Docker Compose (Recommended)

```bash
# Build and start both servers
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop servers
docker-compose down
```

**Access endpoints:**
- FastMCP Server: `http://localhost:8000/mcp` (no trailing slash)
- LowLevel Server: `http://localhost:3000/mcp` (no trailing slash)

**Testing with MCP Inspector:**
```bash
# Open MCP Inspector (it will start on http://localhost:5173 or similar)
npx @modelcontextprotocol/inspector

# Then connect to:
# FastMCP Server: http://localhost:8000/mcp
# LowLevel Server: http://localhost:3000/mcp
```

> **Important:** Do NOT use a trailing slash in the URL. Use `http://localhost:8000/mcp` not `http://localhost:8000/mcp/`

### Option 2: Run Individual Servers

#### Build the image:
```bash
docker build -t mcp-servers .
```

#### Run FastMCP Server:
```bash
docker run -d --name fastmcp -p 8000:8000 mcp-servers mcp-fastmcp-server
```

#### Run LowLevel Server:
```bash
docker run -d --name lowlevel -p 3000:3000 mcp-servers mcp-lowlevel-server --port 3000 --log-level INFO
```

## Docker Commands

### View running containers:
```bash
docker ps
```

### View logs:
```bash
# FastMCP Server
docker logs -f fastmcp

# LowLevel Server
docker logs -f lowlevel

# With Docker Compose
docker-compose logs -f fastmcp-server
docker-compose logs -f lowlevel-server
```

### Stop containers:
```bash
# Individual
docker stop fastmcp lowlevel
docker rm fastmcp lowlevel

# With Docker Compose
docker-compose down
```

### Restart containers:
```bash
# Individual
docker restart fastmcp

# With Docker Compose
docker-compose restart
```

## Health Checks

Both servers include health checks that run every 30 seconds:
```bash
# Check health status
docker ps
# Look for "healthy" in the STATUS column

# With Docker Compose
docker-compose ps
```

## Testing with MCP Inspector

### LowLevel Server (Port 3000) - Working ✅
```
URL: http://localhost:3000/mcp
Transport: streamable-http
```

### FastMCP Server (Port 8000) - Special Requirements ⚠️
The FastMCP server requires clients to send the Accept header with both:
- `application/json` 
- `text/event-stream`

**If MCP Inspector shows 406 errors**, the server is working correctly but the Inspector might not be sending the required Accept headers. 

**Alternative: Use the LowLevel server for testing**, which has more flexible header requirements.

## Troubleshooting

### FastMCP Server Returns 406 Error
This is expected if the client doesn't send proper Accept headers. The server requires:
```
Accept: application/json, text/event-stream
```

Test manually:
```bash
docker exec mcp-fastmcp-server python -c "import httpx; r = httpx.post('http://localhost:8000/mcp', headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, json={'jsonrpc': '2.0', 'method': 'initialize', 'id': 1, 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'test', 'version': '1.0'}}}, timeout=5); print(f'Status: {r.status_code}')"
```

### Check if ports are available:
```powershell
# Windows PowerShell
netstat -an | findstr "8000"
netstat -an | findstr "3000"
```

### View container details:
```bash
docker inspect fastmcp
docker inspect lowlevel
```

### Access container shell:
```bash
docker exec -it fastmcp /bin/bash
```

### Rebuild after code changes:
```bash
docker-compose up --build --force-recreate
```

## Network Configuration

The servers run in an isolated bridge network (`mcp-network`) to avoid networking conflicts. Both servers bind to `0.0.0.0` inside containers to accept external connections properly.

## Environment Variables

You can customize server behavior using environment variables in `docker-compose.yml`:
- `PYTHONUNBUFFERED=1` ensures real-time log output

## Docker Desktop

The setup is optimized for Docker Desktop on Windows:
- Proper port mapping (host:container)
- Health checks for monitoring
- Auto-restart on failure
- Isolated networking to prevent conflicts
