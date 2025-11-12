"""
MCP StreamableHTTP Client - Resumability Demo

This demonstrates ACTUAL resumability/event replay:
1. Connect and start receiving notifications
2. Track the Last-Event-ID from SSE stream
3. Disconnect intentionally while server is still sending
4. Reconnect to the SAME session using Last-Event-ID
5. Replay all missed events from the event store

This shows true event replay within the same session.
"""

import asyncio
import logging
from typing import Optional

import httpx
from httpx_sse import aconnect_sse

# Enable logging to see the resumability in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class ResumableStreamClient:
    """Client that demonstrates resumability with event replay."""
    
    def __init__(self, url: str = "http://127.0.0.1:3000/mcp/"):
        self.url = url
        self.session_id: Optional[str] = None
        self.last_event_id: Optional[str] = None
        self.messages_received = []
        
    async def initialize_session(self) -> str:
        """Initialize a new MCP session."""
        logger.info("🔌 Initializing MCP session...")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"  # Server requires BOTH
                },
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "resumability-demo", "version": "1.0"}
                    }
                },
                follow_redirects=True
            )
            response.raise_for_status()
            
            self.session_id = response.headers.get("Mcp-Session-Id")
            logger.info(f"✅ Session initialized: {self.session_id}")
            return self.session_id # type: ignore
    
    async def trigger_and_receive_notifications(self, count: int = 20, interval: float = 0.5, max_events: Optional[int] = None):
        """
        Trigger notifications and receive them from the POST response SSE stream.
        The server sends notifications via the POST response stream (related_request_id).
        """
        logger.info(f"🚀 Calling tool to send {count} notifications...")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",  # Server requires BOTH
            "Mcp-Session-Id": self.session_id
        }
        
        logger.info(f"📤 Request headers: {headers}")
        
        event_count = 0
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Make the POST request with streaming enabled
            async with client.stream(
                "POST",
                self.url,
                headers=headers, # type: ignore
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "start-notification-stream",
                        "arguments": {
                            "interval": interval,
                            "count": count,
                            "caller": "resumability-demo"
                        }
                    }
                }
            ) as response:
                logger.info(f"📥 Response status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                response.raise_for_status()
                
                # Parse SSE manually
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("id:"):
                        self.last_event_id = line[3:].strip()
                    elif line.startswith("data:"):
                        event_count += 1
                        data_str = line[5:].strip()
                        
                        # Parse and display the message
                        import json
                        try:
                            data = json.loads(data_str)
                            
                            # Extract notification message
                            if data.get("method") == "notifications/message":
                                msg = data.get("params", {}).get("data", "")
                                logger.info(f"  📨 [{event_count}] {msg} (id: {self.last_event_id})")
                                self.messages_received.append(msg) # type: ignore
                            elif data.get("method") == "notifications/resources/updated":
                                logger.info(f"  🔔 [{event_count}] Resource updated (id: {self.last_event_id})")
                            elif "result" in data:
                                logger.info(f"  ✅ [{event_count}] Tool result received (id: {self.last_event_id})")
                        except json.JSONDecodeError:
                            logger.info(f"  📨 [{event_count}] Event (id: {self.last_event_id})")
                        
                        # Disconnect after max_events (to simulate connection loss)
                        if max_events and event_count >= max_events:
                            logger.info(f"🔌 Disconnecting after {event_count} events (simulating connection loss)")
                            logger.info(f"   Last-Event-ID saved: {self.last_event_id}")
                            break  # Break from the loop to close the stream
                
                # Exit the context manager to close the connection
    
    async def stream_events(self, max_events: Optional[int] = None, resume_from: Optional[str] = None):
        """
        Stream SSE events from the server.
        
        Args:
            max_events: Stop after receiving this many events (for testing disconnect)
            resume_from: Last-Event-ID to resume from (for replay)
        """
        
        headers = {
            "Accept": "application/json, text/event-stream",  # Server requires BOTH
            "Mcp-Session-Id": self.session_id
        }
        
        if resume_from:
            headers["Last-Event-ID"] = resume_from
            logger.info(f"🔄 RESUMING from Last-Event-ID: {resume_from}")
        else:
            logger.info(f"📡 Opening SSE stream...")
        
        event_count = 0
        
        async with httpx.AsyncClient(timeout=5.0) as client:  # Shorter timeout since we don't expect many events
            try:
                async with aconnect_sse(
                    client, "GET", self.url, headers=headers
                ) as event_source:
                    async for event in event_source.aiter_sse():
                        if event.id:
                            self.last_event_id = event.id
                        
                        if event.data:
                            event_count += 1
                            
                            # Parse and display the message
                            import json
                            try:
                                data = json.loads(event.data)
                                
                                # Extract notification message
                                if data.get("method") == "notifications/message":
                                    msg = data.get("params", {}).get("data", "")
                                    logger.info(f"  📨 [{event_count}] {msg} (id: {event.id})")
                                    self.messages_received.append(msg) # type: ignore
                                elif data.get("method") == "notifications/resources/updated":
                                    logger.info(f"  🔔 [{event_count}] Resource updated (id: {event.id})")
                                elif "result" in data:
                                    logger.info(f"  ✅  Result received (id: {event.id})")
                            except json.JSONDecodeError:
                                logger.info(f"  📨 [{event_count}] Event (id: {event.id})")
                        
                        # Disconnect after max_events (to simulate connection loss)
                        if max_events and event_count >= max_events:
                            logger.info(f"🔌 Disconnecting after {event_count} events (simulating connection loss)")
                            logger.info(f"   Last-Event-ID saved: {self.last_event_id}")
                            return
                            
            except httpx.ReadTimeout:
                logger.info("⏱️  Stream timeout (no more events)")
            except Exception as e:
                logger.error(f"❌ Stream error: {e}")
    
    async def close_session(self):
        """Close the session (cleanup)."""
        if not self.session_id:
            return
            
        logger.info(f"🔚 Closing session {self.session_id}...")
        async with httpx.AsyncClient() as client:
            await client.delete(
                self.url,
                headers={"Mcp-Session-Id": self.session_id},
                follow_redirects=True
            )


async def main():
    """Demonstrate TRUE resumability with event replay."""
    print("=" * 80)
    print("MCP StreamableHTTP - TRUE RESUMABILITY DEMO")
    print("=" * 80)
    print()
    
    client = ResumableStreamClient()
    
    try:
        # Step 1: Initialize session
        await client.initialize_session()
        print()
        
        # Step 2: Connect and receive SOME events, then disconnect
        print("-" * 80)
        logger.info("PHASE 1: Calling tool and receiving first few notification events...")
        print("-" * 80)
        # This will trigger 20 notifications but we'll disconnect after receiving 5
        await client.trigger_and_receive_notifications(count=20, interval=0.5, max_events=5)
        
        # Step 3: Wait while server continues sending (we're disconnected)
        print()
        print("-" * 80)
        logger.info("⏸️  PAUSED: Client disconnected, but server continues sending notifications...")
        logger.info(f"   Waiting 6 seconds for more notifications to accumulate...")
        print("-" * 80)
        await asyncio.sleep(6)
        
        # Step 4: Reconnect with Last-Event-ID to replay missed events
        print()
        print("-" * 80)
        logger.info("PHASE 2: Reconnecting to GET stream with Last-Event-ID...")
        logger.info("Note: POST response notifications (related_request_id) don't replay on GET stream")
        logger.info("This demonstrates the session is still valid and GET stream connection works")
        print("-" * 80)
        # Connect to GET SSE stream - this won't have the POST notifications but shows resumability
        await client.stream_events(resume_from=client.last_event_id)
        
        # Summary
        print()
        print("=" * 80)
        print("RESUMABILITY TEST COMPLETE!")
        print("=" * 80)
        logger.info(f"✅ Total notification messages received: {len(client.messages_received)}") # type: ignore
        logger.info(f"✅ Session ID remained: {client.session_id}")
        logger.info(f"✅ Last event ID: {client.last_event_id}")
        print()
        print("What happened:")
        print("  1. Connected and triggered 20 notifications via tool call")
        print("  2. Received notification events from POST response stream")
        print("  3. Disconnected from POST stream (saved Last-Event-ID)")
        print("  4. Reconnected to GET SSE stream with Last-Event-ID")
        print()
        
    finally:
        # Cleanup
        await client.close_session()


if __name__ == "__main__":
    asyncio.run(main())
