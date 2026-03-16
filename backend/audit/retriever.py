"""
DEALBOT — Audit Trail Retriever
=================================

Allows users to query past negotiation history via Icarus.

Example user queries:
    "Show me my last deal"
    "What was the negotiation history for the logo design?"
    "List all deals from today"
"""

import json
import time
from typing import List, Optional


class AuditRetriever:
    """
    Retrieves and formats past negotiation audit trails.

    In production, this queries WeilChain on-chain records.
    Currently uses an in-memory store for demo purposes.
    """

    def __init__(self):
        self._deals: List[dict] = []

    def store_deal(self, deal_record: dict) -> None:
        """Store a completed deal record for later retrieval."""
        deal_record["stored_at"] = int(time.time())
        self._deals.append(deal_record)

    def get_latest_deal(self) -> Optional[dict]:
        """Retrieve the most recent deal."""
        if not self._deals:
            return None
        return self._deals[-1]

    def get_all_deals(self) -> List[dict]:
        """Retrieve all stored deals."""
        return list(self._deals)

    def search_deals(self, keyword: str) -> List[dict]:
        """Search deals by keyword in the JSON representation."""
        keyword_lower = keyword.lower()
        results = []
        for deal in self._deals:
            deal_str = json.dumps(deal, default=str).lower()
            if keyword_lower in deal_str:
                results.append(deal)
        return results

    def format_deal_history(self, deal: dict) -> str:
        """
        Format a single deal into Icarus chat-friendly output.
        Matches the format from dealbot_architecture.md §5.2.
        """
        result = deal.get("result", {})
        receipt = deal.get("receipt", {})

        if result.get("status") == "SUCCESS":
            # Build round-by-round log
            trail_lines = []
            for entry in result.get("audit_trail", []):
                phase = "Your Agent" if entry["phase"] == "buyer_eval" else "Seller Agent"
                trail_lines.append(
                    f"  [Round {entry['round']}] {phase}: {entry['price']} WUSD"
                )

            trail_text = "\n".join(trail_lines) if trail_lines else "  No rounds recorded"

            return (
                f"Deal ID: {receipt.get('receipt_id', 'N/A')}\n"
                f"Date: {_format_timestamp(deal.get('stored_at', 0))}\n"
                f"Service: {deal.get('service', 'N/A')}\n"
                f"Final Price: {result.get('price', 'N/A')} WUSD\n"
                f"Delivery: {result.get('days', 'N/A')} days\n"
                f"\nNegotiation Timeline:\n"
                f"{trail_text}\n"
                f"\nStatus: Completed ✓\n"
                f"WeilChain Receipt: {receipt.get('deal_hash', 'N/A')[:16]}..."
            )
        else:
            return (
                f"Deal ID: {receipt.get('receipt_id', 'N/A')}\n"
                f"Date: {_format_timestamp(deal.get('stored_at', 0))}\n"
                f"Status: No Deal ✗\n"
                f"Reason: {result.get('reason', 'BATNA threshold not met')}"
            )


def _format_timestamp(ts: int) -> str:
    """Convert UNIX timestamp to human-readable date."""
    if ts == 0:
        return "Unknown"
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime("%B %d, %Y, %H:%M IST")
