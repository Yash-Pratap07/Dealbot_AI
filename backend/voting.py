"""
Multi-LLM Voting System
  GPT    → aggressive threshold (buyer-friendly)
  Claude → balanced threshold
  Gemini → conservative threshold (seller-friendly)
Majority vote (≥ 2) decides final outcome.
"""
import asyncio

# Each model has a slightly different acceptable price range relative to market
_THRESHOLDS = {
    "GPT":    (0.80, 1.10),
    "Claude": (0.85, 1.15),
    "Gemini": (0.90, 1.20),
}

_REASONING = {
    "GPT": {
        "ACCEPT": "Price aligns with market demand. Buyer gets fair value. I vote ACCEPT.",
        "REJECT": "Price deviates significantly from expected range. I vote REJECT.",
    },
    "Claude": {
        "ACCEPT": "Balanced analysis: both parties gain from this deal. ACCEPT.",
        "REJECT": "Price falls outside balanced fair zone. Recommend more negotiation.",
    },
    "Gemini": {
        "ACCEPT": "Market data supports this price point. Deal is sustainable. ACCEPT.",
        "REJECT": "Price signals potential unfairness. More rounds needed. REJECT.",
    },
}


def majority_vote(votes: list[str]) -> str:
    """Per spec: accept_count >= 2 → ACCEPT, else REJECT."""
    accept_count = sum(1 for v in votes if v == "ACCEPT")
    return "ACCEPT" if accept_count >= 2 else "REJECT"


async def _model_vote(model: str, final_price: float, market_price: float) -> dict:
    """Simulate one model's independent vote."""
    await asyncio.sleep(0.05)
    low_m, high_m = _THRESHOLDS[model]
    accepted = (market_price * low_m) <= final_price <= (market_price * high_m)
    verdict = "ACCEPT" if accepted else "REJECT"
    confidence = round(
        max(0.0, 1.0 - abs(final_price - market_price) / max(market_price, 1)) * 100, 1
    )
    return {
        "model":      model,
        "vote":       verdict,
        "confidence": confidence,
        "reasoning":  _REASONING[model][verdict],
    }


async def majority_vote_decision(
    final_price: float,
    market_price: float,
    history: list[dict],
) -> dict:
    """Run all 3 model votes concurrently and apply majority rule."""
    results = await asyncio.gather(
        _model_vote("GPT",    final_price, market_price),
        _model_vote("Claude", final_price, market_price),
        _model_vote("Gemini", final_price, market_price),
    )
    labels   = [r["vote"] for r in results]
    decision = majority_vote(labels)
    return {
        "votes":         list(results),
        "decision":      decision,
        "accept_count":  labels.count("ACCEPT"),
        "reject_count":  labels.count("REJECT"),
    }
