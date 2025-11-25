"""
StreamableHTTP MCP Server with FastMCP and ServerSession Management

This example demonstrates caching with MCP:
- StreamableHTTP transport
- Logging and Notifications
- Memory/state management via lifespan
- Caching demonstration with process_and_cache tool
- Session management (stateful mode)

Run from the repository root:
    uv run mcp-fastmcp-server
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import AnyUrl

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession


# Mock classes for demonstration
class Database:
    """Mock database for state management."""
    
    async def connect(self) -> "Database":
        print(f"[{datetime.now()}] Database connected")
        return self
    
    async def disconnect(self) -> None:
        print(f"[{datetime.now()}] Database disconnected")
    
    async def query(self, sql: str) -> list[dict[str, Any]]:
        return [{"id": 1, "data": f"Result for: {sql}"}]


class Cache:
    """Mock cache for session data."""
    
    def __init__(self):
        self.data: dict[str, Any] = {}
    
    async def get(self, key: str) -> Any:
        return self.data.get(key)
    
    async def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        print(f"[{datetime.now()}] Cache updated: {key} = {value}")


@dataclass
class AppState:
    """Application state with shared resources."""
    db: Database
    cache: Cache
    metrics: dict[str, int]


# Lifespan for memory/state management
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppState]:
    """Manage application lifecycle and shared resources."""
    print(f"[{datetime.now()}] Server starting up...")
    
    # Initialize resources
    db = await Database().connect()
    cache = Cache()
    metrics: dict[str, int] = {"requests": 0, "errors": 0}
    
    try:
        yield AppState(db=db, cache=cache, metrics=metrics)
    finally:
        # Cleanup
        print(f"[{datetime.now()}] Server shutting down...")
        print(f"[{datetime.now()}] Total requests: {metrics['requests']}")
        await db.disconnect()


# Create FastMCP server with caching demonstration
mcp = FastMCP(
    "CachingDemoServer",
    instructions="MCP server demonstrating caching with process_and_cache tool",
    lifespan=app_lifespan,
    log_level="DEBUG",
)
low_level_server = mcp._mcp_server

@mcp.tool()
async def process_and_cache(
    data: str,
    ctx: Context[ServerSession, AppState] = None,  # type: ignore
) -> str:
    """Process hotel booking data with caching demonstration."""
    # Access shared state
    app_state = ctx.request_context.lifespan_context
    app_state.metrics["requests"] += 1
    
    # Logging
    await ctx.info(f"Processing request {app_state.metrics['requests']}")
    await ctx.debug(f"Input data: {data}")
    
    # Check cache
    cache_key = f"result:{data}"
    cached = await app_state.cache.get(cache_key)
    if cached:
        await ctx.info("Returning cached result")
        return f"Cached: {cached}"
    
    # Simulate work with database
    db_result = await app_state.db.query(f"SELECT * FROM data WHERE input = '{data}'")
    result = f"Processed {data}: {db_result[0]['data']}"
    
    # Store in cache
    await app_state.cache.set(cache_key, result)
    
    await ctx.info(f"Processing complete. Total requests: {app_state.metrics['requests']}")
    
    return result


@mcp.tool()
async def get_metrics(ctx: Context[ServerSession, AppState] = None) -> dict[str, int]:  # type: ignore
    """Get server metrics from shared state."""
    app_state = ctx.request_context.lifespan_context
    
    await ctx.info("Retrieving metrics")
    
    return {
        "total_requests": app_state.metrics["requests"],
        "total_errors": app_state.metrics["errors"],
        "cache_size": len(app_state.cache.data),
    }

# Example of streaming notifications with session management
@mcp.tool()
async def stream_notifications(
    count: int,
    interval: float = 1.0,
    ctx: Context[ServerSession, AppState] = None,  # type: ignore
) -> str:
    """Send streaming notifications with session management."""
    import anyio
    
    await ctx.info(f"Starting notification stream: {count} messages")
    
    for i in range(count):
        # Send log notification
        await ctx.session.send_log_message(
            level="info",
            data=f"Notification {i + 1}/{count}",
            logger="stream",
            # Associate with current request for proper streaming
            related_request_id=ctx.request_id,
        )
        
        await ctx.report_progress(
            progress=(i + 1) / count,
            message=f"Sent {i + 1}/{count} notifications",
        )
        
        if i < count - 1:
            await anyio.sleep(interval)
    
    # Notify about resource changes
    await ctx.session.send_resource_list_changed()
    
    return f"Sent {count} notifications"


# add resources and prompts as needed...
@mcp.resource("state://metrics")
async def metrics_resource(ctx: Context[ServerSession, AppState]) -> str:
    """Expose metrics as a resource."""
    app_state = ctx.request_context.lifespan_context
    
    return f"""
Server Metrics:
- Total Requests: {app_state.metrics["requests"]}
- Total Errors: {app_state.metrics["errors"]}
- Cache Size: {len(app_state.cache.data)}
- Cache Keys: {list(app_state.cache.data.keys())}
"""


@mcp.resource("state://cache/{key}")
async def cache_resource(key: str, ctx: Context[ServerSession, AppState]) -> str:
    """Read from cache by key."""
    app_state = ctx.request_context.lifespan_context
    value = await app_state.cache.get(key)
    
    if value:
        return f"Cache[{key}] = {value}"
    return f"Cache[{key}] = (not found)"



def main():
    """Main entry point for the MCP server."""
    import os
    import uvicorn
    
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    print(f"""
Starting MCP Caching Demo Server
Features:
  ✓ StreamableHTTP transport
  ✓ Memory/state management (lifespan)
  ✓ Caching demonstration (process_and_cache tool)
  ✓ Session management (stateful)
  ✓ Shared resources (database, cache)

Server will be available at: http://{host}:{port}/mcp
    """)
    
    # Monkey patch uvicorn.run to use custom host and port
    original_run = uvicorn.run
    
    def patched_run(app, **kwargs):
        kwargs['host'] = host
        kwargs['port'] = port
        return original_run(app, **kwargs)
    
    uvicorn.run = patched_run
    
    # Run with StreamableHTTP transport
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
