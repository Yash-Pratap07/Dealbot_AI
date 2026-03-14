"""
Memory System — DealBot AI learns from past negotiations.

Tracks:
  - Average accepted price per product
  - Common / successful buyer strategies

ai learn from past deals — per spec.
"""
import json
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "negotiation_memory.json"


def _load() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(data: dict) -> None:
    MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_memory_context(product: str) -> dict:
    """
    Load memory for a product.
    Returns: avg_accepted_price, best_strategy, deal_count.
    """
    data  = _load()
    entry = data.get(product.lower())
    if not entry or entry.get("count", 0) == 0:
        return {"has_memory": False, "product": product}

    avg          = round(entry["total_price"] / entry["count"], 2)
    strategies   = entry.get("strategies", {})
    best_strategy = max(strategies, key=strategies.get) if strategies else "balanced"
    return {
        "has_memory":             True,
        "product":                product,
        "avg_accepted_price":     avg,
        "deal_count":             entry["count"],
        "best_strategy":          best_strategy,
        "strategy_success_counts": strategies,
    }


def save_to_memory(product: str, final_price: float, strategy: str) -> None:
    """
    Record a completed deal so the AI learns from past deals.
    """
    data = _load()
    key  = product.lower()
    if key not in data:
        data[key] = {"total_price": 0.0, "count": 0, "strategies": {}}
    data[key]["total_price"] += final_price
    data[key]["count"]       += 1
    strats = data[key]["strategies"]
    strats[strategy] = strats.get(strategy, 0) + 1
    _save(data)
