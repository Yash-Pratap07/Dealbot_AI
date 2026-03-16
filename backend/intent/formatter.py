"""
DEALBOT — Intent Formatter
============================

Formats negotiation results and deal summaries into structured
messages for the Icarus chat interface.
"""

import json
from typing import Optional


def format_deal_summary(result: dict) -> str:
    """
    Format a negotiation result into a human-readable deal summary
    for display in the Icarus chat interface.
    """
    if result["status"] == "SUCCESS":
        return (
            f"✅ **Deal Reached!**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"  💰 **Final Price:** {result['price']} WUSD\n"
            f"  📅 **Delivery:** {result['days']} days\n"
            f"  🔄 **Rounds:** {result['rounds']}\n"
            f"  🤝 **Accepted By:** {result.get('accepted_by', 'N/A')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"  Awaiting your approval to execute on WeilChain."
        )
    else:
        return (
            f"❌ **No Deal Reached**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"  📋 **Reason:** {result.get('reason', 'BATNA threshold not met')}\n"
            f"  🔄 **Rounds Attempted:** 10 (max)\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"  The agents could not find a mutually acceptable deal.\n"
            f"  Try adjusting your budget or timeline constraints."
        )


def format_approval_request(deal_summary: dict) -> str:
    """
    Format the approval request shown to the user via icarus.request_approval().
    """
    return (
        f"🤝 **DEAL APPROVAL REQUEST**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  **Status:** {deal_summary.get('deal_status', 'N/A')}\n"
        f"  **Price:** {deal_summary.get('final_price', 'N/A')} WUSD\n"
        f"  **Delivery:** {deal_summary.get('delivery_days', 'N/A')} days\n"
        f"  **Rounds:** {deal_summary.get('negotiation_rounds', 'N/A')}\n"
        f"  **Receipt Hash:** `{deal_summary.get('deal_hash', 'N/A')[:16]}...`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  Reply **APPROVE** to execute on WeilChain.\n"
        f"  Reply **REJECT** to cancel.\n"
        f"  Reply **REVISE** to modify terms and re-negotiate."
    )


def format_agent_config(parsed_intent: dict) -> str:
    """
    Format the parsed intent into a readable agent configuration summary.
    """
    return (
        f"🤖 **Agent Configuration**\n"
        f"  📦 Service: {parsed_intent['service']}\n"
        f"  💰 Budget: {parsed_intent['budget']} WUSD\n"
        f"  📅 Timeline: {parsed_intent['days']} days\n"
        f"  ⚖️  Weights: Price={parsed_intent['w_price']}, Time={parsed_intent['w_time']}\n"
        f"  📋 Deliverables: {', '.join(parsed_intent['deliverables'])}"
    )


def format_round_log(audit_trail: list) -> str:
    """
    Format the round-by-round audit trail into a readable negotiation log.
    """
    lines = ["📜 **Negotiation Log**", ""]

    for entry in audit_trail:
        phase_icon = "🛒" if entry["phase"] == "buyer_eval" else "🏪"
        phase_label = "Buyer" if entry["phase"] == "buyer_eval" else "Seller"

        lines.append(
            f"  [Round {entry['round']}] {phase_icon} {phase_label}: "
            f"{entry['price']} WUSD | U={entry['utility']}"
        )

    return "\n".join(lines)


def format_market_data(market_data: dict) -> str:
    """
    Format MCP market data response for display.
    """
    data = market_data.get("data", {})
    return (
        f"📊 **Market Data** ({market_data.get('category', 'N/A')})\n"
        f"  Low:  {data.get('low_end', 'N/A')} WUSD\n"
        f"  Avg:  {data.get('average', 'N/A')} WUSD\n"
        f"  High: {data.get('high_end', 'N/A')} WUSD\n"
        f"  Typical Delivery: {data.get('typical_delivery_days', 'N/A')} days"
    )
