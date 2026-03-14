"""
Evaluator AI — checks if a negotiated price is fair.
Returns ACCEPT or NEGOTIATE (per spec).

Also provides:
  - DealAgent: Mathematical utility scoring U(x) = w_p·P(x) + w_t·T(x)
  - BidPayload: Structured, SHA-256 hashed bid for audit trail integrity.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import List

# Fair price window: ±15% of market price
FAIR_PRICE_RANGE = (0.85, 1.15)


def evaluate_deal(
    final_price: float,
    market_price: float,
    fair_range: tuple[float, float] = FAIR_PRICE_RANGE,
) -> dict:
    """
    evaluateDeal(price, config) — check if price is in fair range.
    Returns ACCEPT or NEGOTIATE.
    """
    lower = market_price * fair_range[0]
    upper = market_price * fair_range[1]
    deviation = round((final_price - market_price) / market_price * 100, 1)

    if lower <= final_price <= upper:
        verdict = "ACCEPT"
        confidence = round(max(0.0, 1.0 - abs(deviation) / 15.0) * 100, 1)
        message = (
            f"Deal price ${final_price:,.2f} is within ±15% of market "
            f"${market_price:,.2f} (deviation {deviation:+.1f}%). Fair deal."
        )
    else:
        verdict = "NEGOTIATE"
        confidence = round(min(abs(deviation) / 15.0, 1.0) * 100, 1)
        if final_price > upper:
            message = (
                f"${final_price:,.2f} is {deviation:+.1f}% above market "
                f"${market_price:,.2f}. Price too high — keep negotiating."
            )
        else:
            message = (
                f"${final_price:,.2f} is {deviation:+.1f}% below market "
                f"${market_price:,.2f}. Suspiciously cheap — investigate."
            )

    return {
        "verdict": verdict,
        "confidence": confidence,
        "deviation": deviation,
        "market_price": market_price,
        "fair_range": [round(lower, 2), round(upper, 2)],
        "message": message,
    }


# ────────────────────────────────────────────────────────────────────
# DealAgent — Mathematical Utility Scoring
# ────────────────────────────────────────────────────────────────────

class DealAgent:
    """
    Implements utility function: U(x) = w_p · P(x) + w_t · T(x)

    Where:
        - w_p, w_t are user-assigned importance weights (sum to 1.0)
        - P(x) is the normalized price score
        - T(x) is the normalized timeline score
        - A bid is accepted when U(x) >= threshold (default 0.65)
    """

    def __init__(
        self,
        role: str,
        max_budget: float,
        target_days: int,
        w_price: float = 0.7,
        w_time: float = 0.3,
    ):
        self.role = role
        self.max_budget = max_budget
        self.target_days = target_days
        self.w_price = w_price
        self.w_time = w_time
        self.utility_threshold = 0.65

    def calculate_utility(self, proposed_price: float, proposed_days: int) -> float:
        """
        Core utility: U(x) = w_p · P(x) + w_t · T(x)
        Returns a float in [0, 1]. Returns 0.0 for dealbreaker proposals.
        """
        if self.role == "buyer":
            if proposed_price > self.max_budget:
                return 0.0
            p_score = 1.0 - (proposed_price / self.max_budget)
        else:
            if proposed_price < self.max_budget:
                return 0.0
            p_score = min((proposed_price - self.max_budget) / self.max_budget, 1.0)

        max_acceptable_days = self.target_days * 2
        if proposed_days > max_acceptable_days:
            return 0.0
        t_score = 1.0 - (proposed_days / max_acceptable_days)

        u_x = (self.w_price * p_score) + (self.w_time * t_score)
        return round(u_x, 4)

    def generate_counter_offer(self, current_price: float, current_days: int):
        """Move 10% closer to the counterparty's offer."""
        if self.role == "buyer":
            new_price = min(current_price * 0.9, self.max_budget)
        else:
            new_price = max(current_price * 1.1, self.max_budget)
        return round(new_price, 2), current_days


# ────────────────────────────────────────────────────────────────────
# BidPayload — Structured, Auditable Bid
# ────────────────────────────────────────────────────────────────────

@dataclass
class BidPayload:
    """
    Standard bid payload with SHA-256 proposal_id for audit trails.
    """
    price: float
    days: int
    round_num: int
    agent_role: str
    deliverables: List[str] = field(default_factory=lambda: ["Standard deliverables"])
    proposal_id: str = field(default="")

    def __post_init__(self):
        if not self.proposal_id:
            self.proposal_id = self._generate_proposal_id()

    def _generate_proposal_id(self) -> str:
        """SHA-256 hash of canonical terms → deterministic proposal_id."""
        canonical = json.dumps({
            "price": self.price,
            "days": self.days,
            "round_num": self.round_num,
            "agent_role": self.agent_role,
            "deliverables": sorted(self.deliverables),
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)
