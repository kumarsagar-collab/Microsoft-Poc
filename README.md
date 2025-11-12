# MCP StreamableHTTP Servers

This repository contains two MCP (Model Context Protocol) server implementations demonstrating StreamableHTTP transport.

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

## Installation

```bash
uv sync
```

## Requirements

- Python >= 3.10
- Dependencies managed via `uv`
