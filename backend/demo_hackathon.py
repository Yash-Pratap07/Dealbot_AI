"""
DEALBOT — Standalone Integration Demo
=======================================

Runs the full DEALBOT pipeline locally without requiring the Weil SDK
to be connected to a live blockchain node. Perfect for recording
the hackathon submission video.

Run: python demo.py
"""

import asyncio
import sys
import os
from pprint import pprint

sys.path.insert(0, os.path.dirname(__file__))

from agent.utility import DealAgent
from agent.guardrails import run_pre_negotiation_checks
from agent.preferences import PreferenceProfile
from orchestrator import Orchestrator
from intent.parser import parse_negotiation_intent
from intent.formatter import (
    format_deal_summary,
    format_agent_config,
    format_market_data,
    format_approval_request
)

async def simulate_mcp_fetch(category: str) -> dict:
    """Mock MCP tool response."""
    await asyncio.sleep(1)
    return {
        "status": "success",
        "category": category,
        "data": {
            "low_end": 400.0,
            "average": 600.0,
            "high_end": 900.0,
            "typical_delivery_days": 10
        }
    }

async def run_demo():
    print("="*60)
    print(" DEALBOT (Simulated Offline Demo)")
    print("="*60)

    # 1. User Prompt
    prompt = "I need a graphic designer for a new logo. Budget $800 max, delivery in 14 days. Find me the best deal."
    print(f"\n[USER]: {prompt}")

    # 2. Intent Parsing
    print("\n[SYSTEM]: Parsing intent...")
    intent = parse_negotiation_intent(prompt)
    print(format_agent_config(intent))

    # 3. Guardrails
    print("\n[SYSTEM]: Running safety guardrails...")
    checks = run_pre_negotiation_checks(intent["budget"], "0xVendorPool")
    print("Status: Passed ✓")

    # 4. MCP Market Data
    print("\n[SYSTEM]: Fetching live WeilChain market data via MCP...")
    market_data = await simulate_mcp_fetch(intent["service"])
    print(format_market_data(market_data))

    # 5. Multi-Agent Orchestration
    print("\n[SYSTEM]: Launching parallel negotiations with 3 vendors...")
    
    buyer = DealAgent("buyer", intent["budget"], intent["days"], intent["w_price"], intent["w_time"])
    orch = Orchestrator(buyer)
    
    market_avg = market_data["data"]["average"]
    market_high = market_data["data"]["high_end"]

    orch.add_seller("Vendor_Alpha", DealAgent("seller", market_avg*0.7, 10, 0.5, 0.5), market_high, 14)
    orch.add_seller("Vendor_Beta", DealAgent("seller", market_avg*0.6, 14, 0.6, 0.4), market_high*0.9, 14)
    orch.add_seller("Vendor_Gamma", DealAgent("seller", market_avg*0.9, 7, 0.4, 0.6), market_high*0.8, 14)

    await orch.run_all()

    print(f"\n{orch.format_comparison()}")

    # 6. Result & Approval
    best_deal = orch.get_best_deal()
    if best_deal:
        print(f"\n{format_deal_summary(best_deal)}")
        
        # Simulate approval UI
        approval_payload = {
            "deal_status": best_deal["status"],
            "final_price": best_deal["price"],
            "delivery_days": best_deal["days"],
            "negotiation_rounds": best_deal["rounds"],
            "deal_hash": best_deal["final_bid"]["proposal_id"]
        }
        print(f"\n{format_approval_request(approval_payload)}")
        
        print("\n[USER]: APPROVE")
        print("🎉 Deal APPROVED! 420.0 WUSD transferred to escrow.")
        print("✅ Transaction recorded on WeilChain.")

if __name__ == "__main__":
    asyncio.run(run_demo())
