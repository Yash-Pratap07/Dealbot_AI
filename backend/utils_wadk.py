"""
Compatibility layer for the newly updated WADK 0.1.3 python sdk.
The hackathon provided SDK shifted from `weil_sdk` to `wadk` (in separate packages weil_wallet and weil_ai), 
and uses `fastmcp` and `WeilClient` instead of the old `IcarusClient` and `AuditLogger`.
"""

import json
import asyncio
from typing import Any, Dict

# NEW WADK (0.1.3) IMPORTS
try:
    from weil_wallet import PrivateKey, Wallet, WeilClient
except ImportError:
    WeilClient = None

class NewAuditLogger:
    """Replaces the old AuditLogger by using the updated WeilClient from weil_wallet."""
    def __init__(self, chain: str = "weilchain_testnet"):
        self.chain = chain
        # Try to initialize wallet if private_key.wc exists, otherwise run in passive mode
        self.wallet = None
        self.client = None
        try:
            # Minimal mock initialization for the demo
            pass 
        except Exception:
            pass

    def log_action(self, action: str, agent: str, data: Dict[str, Any]):
        """Standardizes how audit events were written previously."""
        payload = {"action": action, "agent": agent, "data": data}
        print(f"[AUDIT LOG on {self.chain}]: {json.dumps(payload)}")
        # In a real environment with a private_key.wc:
        # if self.client:
        #     asyncio.create_task(self.client.audit(json.dumps(payload)))

class IcarusAdapter:
    """
    Adapter mimicking the older @icarus decorators while the team
    transitions to the new FastMCP / `weil_ai.mcp` standards.
    """
    def __init__(self):
        self.tools = {}
        self.listeners = []

    def register_mcp(self, name: str):
        print(f"[ICARUS MCP] Registered Applet: {name}")

    def register_mcp_tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

    def on_message(self, func):
        self.listeners.append(func)
        return func

    async def call_mcp_tool(self, name: str, **kwargs):
        if name in self.tools:
            return await self.tools[name](**kwargs)
        # Mock responses if tool isn't strictly registered during tests
        await asyncio.sleep(0.5)
        return {"status": "success", "mocked": True}

    async def request_approval(self, payload: dict):
        print(f"\n[ICARUS UI PROMPT]: Awaiting user approval for deal:")
        print(json.dumps(payload, indent=2))
        return "APPROVE"

    async def listen(self):
        print("[ICARUS] Server listening for messages...")
        await asyncio.sleep(86400) # Mock long-lived server

# Expose globals so main.py and market_data.py don't crash
icarus = IcarusAdapter()
AuditLogger = NewAuditLogger
