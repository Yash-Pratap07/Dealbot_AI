"""
DEALBOT — MCP External Market Data Integration
================================================

Implements the MCP tools defined in mcp_external_integration.md:

    1. fetch_market_rate(category)
       → Queries external APIs for WUSD pricing bounds.
       → Establishes the agent's baseline P(x) score.

    2. verify_identity(party_wallet)
       → Checks counterparty WeilChain history for reliability.

All MCP tool calls are registered via @icarus.register_mcp_tool()
and their results are appended to the AuditLogger for transparency.
"""

import asyncio
from utils_wadk import icarus
import random

# ---------------------------------------------------------
# MOCK DATABASE: Simulating real-world API responses
# Values represent standard market rates in WUSD
# ---------------------------------------------------------
MARKET_RATES_DB = {
    "freelance_logo_design": {
        "low_end": 150.00,
        "average": 300.00,
        "high_end": 600.00,
        "typical_delivery_days": 5
    },
    "smart_contract_audit": {
        "low_end": 1000.00,
        "average": 2500.00,
        "high_end": 5000.00,
        "typical_delivery_days": 14
    },
    "copywriting_landing_page": {
        "low_end": 200.00,
        "average": 450.00,
        "high_end": 800.00,
        "typical_delivery_days": 3
    }
}


@icarus.register_mcp_tool(
    name="fetch_market_rate",
    description="Fetches current market pricing and timeline data for a specific service category."
)
async def fetch_market_rate(category: str) -> dict:
    """
    Simulates an MCP tool fetching off-chain market data.
    Returns a dictionary containing WUSD pricing bounds and timelines.

    The returned data structure:
        {
            "status": "success",
            "category": "<normalized_key>",
            "data": {
                "low_end": float,    # Minimum market price in WUSD
                "average": float,    # Average market price in WUSD
                "high_end": float,   # Maximum market price in WUSD
                "typical_delivery_days": int
            }
        }
    """
    # Simulate network latency (0.5 to 1.5 seconds)
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Normalize the category string
    search_key = category.lower().replace(" ", "_")

    if search_key in MARKET_RATES_DB:
        return {
            "status": "success",
            "category": search_key,
            "data": MARKET_RATES_DB[search_key]
        }
    else:
        # Fallback for unknown categories to keep the agent moving
        return {
            "status": "success",
            "category": search_key,
            "data": {
                "low_end": 100.00,
                "average": 250.00,
                "high_end": 500.00,
                "typical_delivery_days": 7
            },
            "note": "Estimated fallback data used."
        }


@icarus.register_mcp_tool(
    name="verify_identity",
    description="Checks counterparty WeilChain history for reliability."
)
async def verify_identity(party_wallet: str) -> dict:
    """Simulates checking a wallet's past deal success rate."""
    await asyncio.sleep(0.5)
    return {
        "wallet": party_wallet,
        "successful_deals": random.randint(5, 50),
        "default_rate_percentage": random.uniform(0.0, 2.5),
        "risk_level": "LOW"
    }
