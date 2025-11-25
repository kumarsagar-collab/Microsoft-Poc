# MCP Server Implementations - Technical Overview

## FastMCP Server (`FastMCPServer/server.py`)

### Technical Features
- **High-level abstraction** - Decorator-based tool/resource registration
- **Built-in lifecycle management** - `lifespan` context manager for resource initialization/cleanup
- **State management** - `AppState` dataclass with shared resources (Database, Cache, Metrics)
- **Context injection** - Automatic `Context[ServerSession, AppState]` injection in tools
- **Observability** - Built-in logging, progress reporting via `ctx.info()`, `ctx.debug()`, `ctx.report_progress()`
- **Caching demonstration** - `process_and_cache` tool shows cache-first pattern
- **Resource exposure** - Dynamic resources via `@mcp.resource()` decorator

### Tools
- `process_and_cache(data: str)` - Cache-first data processing with DB fallback
- `get_metrics()` - Server statistics (requests, errors, cache size)
- `stream_notifications(count: int, interval: float)` - Streaming log messages with progress

### Resources
- `state://metrics` - Server metrics snapshot
- `state://cache/{key}` - Direct cache value lookup

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│                   FastMCP Server                        │
├─────────────────────────────────────────────────────────┤
│  Client Request → StreamableHTTP Transport              │
│         ↓                                               │
│  FastMCP Framework (Decorator Registry)                 │
│         ↓                                               │
│  Lifespan Context Manager                               │
│    ├─ Database.connect()                                │
│    ├─ Cache (in-memory dict)                            │
│    └─ Metrics (requests/errors counters)                │
│         ↓                                               │
│  Tool Execution (@mcp.tool)                             │
│    ├─ Auto-inject Context[ServerSession, AppState]     │
│    ├─ Check Cache → Return if hit                       │
│    ├─ Query Database → Process data                     │
│    ├─ Update Cache                                      │
│    └─ ctx.info/debug/report_progress                    │
│         ↓                                               │
│  Response → JSON/SSE Stream                             │
└─────────────────────────────────────────────────────────┘

Flow: Request → Decorator Lookup → State Injection → Cache Check → 
      DB Query → Cache Update → Observability Logging → Response
```

---

## LowLevel MCP Server (`LowLevelMCPServer/server.py`)

### Technical Features
- **Protocol-level implementation** - Direct MCP protocol handling
- **Manual request/response** - Explicit JSON-RPC 2.0 message construction
- **Flexible transport** - Works with any transport layer (HTTP, stdio, SSE)
- **No framework overhead** - Minimal abstractions, full control
- **Custom routing** - Manual tool dispatch and response formatting
- **MCP Inspector compatible** - Standard protocol implementation for debugging

### Tools
- `start-notification-stream(interval: float, count: int, caller: str)` - Sends stream of notifications with configurable timing, demonstrates SSE streaming and resumability

### Architecture
```
┌─────────────────────────────────────────────────────────┐
│                LowLevel MCP Server                      │
├─────────────────────────────────────────────────────────┤
│  Client Request → Starlette ASGI App                    │
│         ↓                                               │
│  StreamableHTTPSessionManager                           │
│    ├─ Parse JSON-RPC 2.0 message                        │
│    ├─ Extract method & params                           │
│    └─ Manage SSE event stream                           │
│         ↓                                               │
│  Manual Tool Dispatch                                   │
│    ├─ Match tool name                                   │
│    ├─ Extract arguments from dict                       │
│    └─ Execute tool logic                                │
│         ↓                                               │
│  Notification Streaming (SSE)                           │
│    ├─ send_log_message() with related_request_id       │
│    ├─ InMemoryEventStore (resumability)                │
│    └─ Last-Event-ID support                             │
│         ↓                                               │
│  Build Response                                         │
│    └─ Manual types.TextContent construction             │
│         ↓                                               │
│  Response → JSON-RPC 2.0 / SSE Stream                   │
└─────────────────────────────────────────────────────────┘

Flow: Request → Session Manager → JSON-RPC Parse → 
      Manual Dispatch → Tool Logic → SSE Notifications → 
      Event Store (resumability) → Response
```

---

## Key Differences

| Aspect | FastMCP | LowLevel MCP |
|--------|---------|--------------|
| **Abstraction** | High-level, decorator-based | Low-level, protocol-aware |
| **State Management** | Built-in lifespan + AppState | Manual implementation |
| **Tool Definition** | `@mcp.tool()` decorator | Manual JSON schema + dispatch |
| **Context** | Auto-injected `Context` object | Manual context passing |
| **Observability** | Built-in logging/progress | Manual implementation |
| **Use Case** | Production agents with state | Protocol learning, simple tools |
| **Complexity** | Higher (framework features) | Lower (minimal code) |
| **Flexibility** | Framework conventions | Full protocol control |

---

## Running the Servers

### FastMCP Server
```bash
# Local
uv run mcp-fastmcp-server

# Docker
docker-compose up mcp-fastmcp-server
```
**Port:** 8000  
**Endpoint:** `http://127.0.0.1:8000/mcp`

### LowLevel Server
```bash
# Local
uv run mcp-lowlevel-server

# Docker
docker-compose up mcp-lowlevel-server
```
**Port:** 3000  
**Endpoint:** `http://127.0.0.1:3000/mcp`

---

## When to Use Which

### Choose FastMCP When:
- Building production AI agents
- Need state management (sessions, cache, DB)
- Want built-in observability
- Rapid development with decorators
- Complex multi-tool systems

### Choose LowLevel When:
- Learning MCP protocol internals
- Need full protocol control
- Building custom transport layers
- Minimal dependencies required
- Debugging with MCP Inspector
