# MCP StreamableHTTP Servers

This repository contains two MCP (Model Context Protocol) server implementations demonstrating StreamableHTTP transport. Each server has different characteristics and is suited for different use cases.

## 🚀 Quick Start

```bash
# Install dependencies
uv sync

# Run FastMCP Server (port 8000)
uv run mcp-fastmcp-server

# Run LowLevel Server (port 3000)
uv run mcp-lowlevel-server
```



⚠️ **Note:** FastMCP requires clients to send `Accept: application/json, text/event-stream` header. MCP Inspector may not send these headers by default.

## Available Servers

### 1. FastMCP Server
High-level MCP server with state management and observability features.

**Run:**
```bash
uv run mcp-fastmcp-server
```

**Endpoint:** `http://127.0.0.1:8000/mcp`

**Features:**
- State management with lifespan context
- Progress tracking and logging
- Cache and database integration
- Tools: `process_data`, `get_metrics`, `stream_notifications`
- Resources: `state://metrics`, `state://cache/{key}`

**Client Requirements:**
```python
import httpx

response = httpx.post(
    "http://localhost:8000/mcp",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"  # Required!
    },
    json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1,
        "params": {...}
    }
)
```

**Testing FastMCP Server (Docker):**

Since FastMCP requires strict Accept headers, test it using this command from PowerShell:

```bash
docker exec mcp-fastmcp-server python -c "import httpx; r = httpx.post('http://localhost:8000/mcp', headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, json={'jsonrpc': '2.0', 'method': 'initialize', 'id': 1, 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'test', 'version': '1.0'}}}, timeout=5); print(f'Status: {r.status_code}'); print(f'Body: {r.text}')"
```

Expected output: `Status: 200` with MCP initialization response.

### 2. LowLevel MCP Server
Low-level MCP server implementation with notification streaming.

**Run:**
```bash
uv run mcp-lowlevel-server
```

**Endpoint:** `http://127.0.0.1:3000/mcp`

**Options:**
- `--port INTEGER` - Server port (default: 3000)
- `--log-level TEXT` - Log level (default: INFO)
- `--json-response` - Use JSON instead of SSE streams

**Example with options:**
```bash
uv run mcp-lowlevel-server --port 3000 --log-level DEBUG
```

**Features:**
- Event store for resumability
- CORS support
- Tool: `start-notification-stream`
- Works with MCP Inspector out-of-the-box

**Client Requirements:**
```python
import httpx

# Standard headers work fine
response = httpx.post(
    "http://localhost:3000/mcp",
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json"  # Standard header
    },
    json={
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": 1,
        "params": {...}
    }
)
```

## 🧪 Testing with MCP Inspector

**✅ Recommended:** Use the LowLevel Server
```
URL: http://localhost:3000/mcp/
```

⚠️ **Important:** The trailing slash is required! Use `http://localhost:3000/mcp/` not `http://localhost:3000/mcp`

**⚠️ Not Recommended:** FastMCP Server requires custom Accept headers that Inspector may not send by default.

## Installation

```bash
uv sync
```

## Requirements

- Python >= 3.10
- Dependencies managed via `uv`
