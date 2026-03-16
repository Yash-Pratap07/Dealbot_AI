"""
DEALBOT — Preference Learning Module
======================================

Learns and adapts agent weight preferences (w_price, w_time) based on
the user's past approval/rejection patterns.

Per architecture doc Phase 2:
    "Advanced conversational features: deal history queries, preference learning"

The system tracks which deals the user approved vs rejected, and shifts
the weight parameters to better align with observed preferences over time.
"""

from typing import List, Optional, Tuple
import json


class PreferenceProfile:
    """
    User preference profile that evolves based on approval history.

    Tracks:
        - Approved deal characteristics (price, timeline, weights)
        - Rejected deal characteristics
        - Running averages that inform future agent configuration
    """

    # Learning rate controls how fast weights adapt
    LEARNING_RATE = 0.1

    def __init__(
        self,
        initial_w_price: float = 0.7,
        initial_w_time: float = 0.3,
    ):
        self.w_price = initial_w_price
        self.w_time = initial_w_time

        self._approved_deals: List[dict] = []
        self._rejected_deals: List[dict] = []

        # Running statistics
        self._avg_approved_price: float = 0.0
        self._avg_approved_days: float = 0.0
        self._avg_rejected_price: float = 0.0
        self._avg_rejected_days: float = 0.0

    # ---------------------------------------------------------------
    # Record Outcomes
    # ---------------------------------------------------------------

    def record_approval(self, price: float, days: int, budget: float) -> None:
        """Record that the user approved a deal at this price/timeline."""
        self._approved_deals.append({
            "price": price,
            "days": days,
            "budget": budget,
            "price_ratio": price / budget if budget > 0 else 0,
        })
        self._update_statistics()
        self._adapt_weights()

    def record_rejection(self, price: float, days: int, budget: float) -> None:
        """Record that the user rejected a deal at this price/timeline."""
        self._rejected_deals.append({
            "price": price,
            "days": days,
            "budget": budget,
            "price_ratio": price / budget if budget > 0 else 0,
        })
        self._update_statistics()
        self._adapt_weights()

    # ---------------------------------------------------------------
    # Weight Adaptation — gradient-free learning
    # ---------------------------------------------------------------

    def _adapt_weights(self) -> None:
        """
        Adapt w_price and w_time based on approval patterns.

        Logic:
            - If user tends to approve cheap deals (low price_ratio) → increase w_price
            - If user tends to approve fast deals (low days) → increase w_time
            - Compare approved vs rejected profiles to determine direction
        """
        if len(self._approved_deals) < 2:
            return  # Not enough data to learn

        # Calculate approved deal tendencies
        approved_price_ratios = [d["price_ratio"] for d in self._approved_deals]
        avg_approved_ratio = sum(approved_price_ratios) / len(approved_price_ratios)

        approved_days = [d["days"] for d in self._approved_deals]
        avg_approved_days = sum(approved_days) / len(approved_days)

        # Compute signals
        # Low price_ratio in approved deals → user cares about price
        price_signal = 1.0 - avg_approved_ratio  # Higher when user approves cheaper deals

        # Low days in approved deals → user cares about speed
        max_days = max(d["days"] for d in self._approved_deals + self._rejected_deals) or 30
        time_signal = 1.0 - (avg_approved_days / max_days)  # Higher when user approves faster

        # Normalize signals
        total_signal = price_signal + time_signal
        if total_signal > 0:
            target_w_price = price_signal / total_signal
            target_w_time = time_signal / total_signal
        else:
            return

        # Smooth update with learning rate
        self.w_price += self.LEARNING_RATE * (target_w_price - self.w_price)
        self.w_time += self.LEARNING_RATE * (target_w_time - self.w_time)

        # Normalize to ensure they still sum to 1.0
        total = self.w_price + self.w_time
        self.w_price = round(self.w_price / total, 4)
        self.w_time = round(self.w_time / total, 4)

    # ---------------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------------

    def _update_statistics(self) -> None:
        """Recompute running averages."""
        if self._approved_deals:
            self._avg_approved_price = sum(d["price"] for d in self._approved_deals) / len(self._approved_deals)
            self._avg_approved_days = sum(d["days"] for d in self._approved_deals) / len(self._approved_deals)

        if self._rejected_deals:
            self._avg_rejected_price = sum(d["price"] for d in self._rejected_deals) / len(self._rejected_deals)
            self._avg_rejected_days = sum(d["days"] for d in self._rejected_deals) / len(self._rejected_deals)

    def get_weights(self) -> Tuple[float, float]:
        """Return current learned (w_price, w_time)."""
        return (self.w_price, self.w_time)

    def get_insights(self) -> dict:
        """Return a summary of learned preferences for display."""
        return {
            "current_weights": {"w_price": self.w_price, "w_time": self.w_time},
            "approved_deals": len(self._approved_deals),
            "rejected_deals": len(self._rejected_deals),
            "avg_approved_price": round(self._avg_approved_price, 2),
            "avg_approved_days": round(self._avg_approved_days, 1),
            "avg_rejected_price": round(self._avg_rejected_price, 2),
            "avg_rejected_days": round(self._avg_rejected_days, 1),
        }

    def format_profile(self) -> str:
        """Format preferences for Icarus chat display."""
        insights = self.get_insights()
        return (
            f"📊 **Your Negotiation Profile**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  ⚖️  Price Weight: {self.w_price:.0%}\n"
            f"  ⏱️  Time Weight:  {self.w_time:.0%}\n"
            f"  ✅  Deals Approved: {insights['approved_deals']}\n"
            f"  ❌  Deals Rejected: {insights['rejected_deals']}\n"
            f"  💰  Avg Approved Price: {insights['avg_approved_price']} WUSD\n"
            f"  📅  Avg Approved Timeline: {insights['avg_approved_days']} days\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"  Weights adapt automatically as you approve/reject more deals."
        )

    def to_dict(self) -> dict:
        """Serialize for persistence."""
        return {
            "w_price": self.w_price,
            "w_time": self.w_time,
            "approved_deals": self._approved_deals,
            "rejected_deals": self._rejected_deals,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PreferenceProfile":
        """Deserialize from saved state."""
        profile = cls(
            initial_w_price=data.get("w_price", 0.7),
            initial_w_time=data.get("w_time", 0.3),
        )
        profile._approved_deals = data.get("approved_deals", [])
        profile._rejected_deals = data.get("rejected_deals", [])
        profile._update_statistics()
        return profile
