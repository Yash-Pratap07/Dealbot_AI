"""
DealBot AI — Safety, Fraud Detection & Agent Guardrails
=========================================================

Combines:
  - Original fraud_check() for price-vs-market analysis
  - Enhanced guardrails (from hackathon) for budget enforcement,
    adversarial detection, concession rate limits, and time-based aborts.
"""

import time
from typing import Optional

# ────────────────────────────────────────────────────────────────────
# Configuration Constants
# ────────────────────────────────────────────────────────────────────

# Fraud detection thresholds
UPPER_FLAG = 2.0       # price > 2× market → FLAG
LOWER_FLAG = 0.30      # price < 30% of market → FLAG (suspiciously cheap)
GAP_FLAG   = 5.0       # seller > 5× buyer → extreme mismatch

# Guardrail constants
MAX_BUDGET_HARD_LIMIT       = 100_000.0   # Absolute ceiling for any single deal
MAX_NEGOTIATION_HOURS       = 24          # Auto-abort after this duration
MIN_PRICE_FLOOR             = 1.0         # No deal below this price
MAX_CONCESSION_RATE         = 0.25        # Max 25% concede per round
LOWBALL_THRESHOLD           = 0.3         # Flag if offer < 30% of reference
HIGH_VALUE_APPROVAL_THRESHOLD = 10_000.0  # Extra confirmation above this


class GuardrailViolation(Exception):
    """Raised when a negotiation violates a safety guardrail."""
    pass


# ────────────────────────────────────────────────────────────────────
# Original Fraud Detection
# ────────────────────────────────────────────────────────────────────

def fraud_check(
    buyer_price: float,
    seller_price: float,
    market_price: float,
) -> str | None:
    """
    Detect:
      - Fake price manipulation
      - Extreme price mismatch
      - Suspiciously low / high prices

    if(price > marketPrice * 2) → FLAG  (per spec)
    Returns a flag string or None.
    """
    if market_price <= 0:
        return None

    if seller_price > market_price * UPPER_FLAG:
        return (
            f"FLAG: Seller ${seller_price:,.2f} is over {UPPER_FLAG}× "
            f"market price ${market_price:,.2f} — possible manipulation"
        )
    if buyer_price > market_price * UPPER_FLAG:
        return (
            f"FLAG: Buyer offer ${buyer_price:,.2f} is over {UPPER_FLAG}× "
            f"market price ${market_price:,.2f} — suspicious wallet"
        )
    if seller_price < market_price * LOWER_FLAG:
        return (
            f"FLAG: Seller ${seller_price:,.2f} is below 30% of market "
            f"${market_price:,.2f} — suspicious listing"
        )
    if buyer_price > 0 and seller_price / max(buyer_price, 0.01) > GAP_FLAG:
        return (
            f"FLAG: Extreme gap — seller ${seller_price:,.2f} "
            f"vs buyer ${buyer_price:,.2f}"
        )
    return None


def is_safe(content: str) -> bool:
    """Legacy content safety check."""
    return bool(content and content.strip())


# ────────────────────────────────────────────────────────────────────
# Budget Guardrails
# ────────────────────────────────────────────────────────────────────

def validate_budget(budget: float) -> None:
    """Ensure budget is within acceptable bounds."""
    if budget <= 0:
        raise GuardrailViolation(
            f"Budget must be positive, got {budget}"
        )
    if budget > MAX_BUDGET_HARD_LIMIT:
        raise GuardrailViolation(
            f"Budget {budget} exceeds hard limit of {MAX_BUDGET_HARD_LIMIT}"
        )


def validate_price_bounds(price: float, max_budget: float, role: str) -> None:
    """Ensure a proposed price doesn't violate the agent's mandate."""
    if price < MIN_PRICE_FLOOR:
        raise GuardrailViolation(
            f"Price {price} below minimum floor of {MIN_PRICE_FLOOR}"
        )
    if role == "buyer" and price > max_budget:
        raise GuardrailViolation(
            f"Buyer price {price} exceeds max budget of {max_budget}"
        )
    if role == "seller" and price < max_budget:
        raise GuardrailViolation(
            f"Seller price {price} below minimum floor of {max_budget}"
        )


def requires_high_value_approval(price: float) -> bool:
    """Check if the deal exceeds the high-value approval threshold."""
    return price >= HIGH_VALUE_APPROVAL_THRESHOLD


# ────────────────────────────────────────────────────────────────────
# Time-Based Guardrails
# ────────────────────────────────────────────────────────────────────

def validate_negotiation_duration(start_time: float) -> None:
    """Auto-abort if negotiation exceeds the maximum allowed duration."""
    elapsed_hours = (time.time() - start_time) / 3600
    if elapsed_hours > MAX_NEGOTIATION_HOURS:
        raise GuardrailViolation(
            f"Negotiation exceeded {MAX_NEGOTIATION_HOURS}-hour time limit "
            f"({elapsed_hours:.1f} hours elapsed). Auto-aborting."
        )


# ────────────────────────────────────────────────────────────────────
# Adversarial Detection
# ────────────────────────────────────────────────────────────────────

def detect_adversarial_pattern(
    current_price: float,
    reference_price: float,
    round_history: list,
) -> Optional[str]:
    """
    Flag suspicious negotiation patterns.

    Checks:
        1. Aggressive lowballing (offer < 30% of reference)
        2. Oscillating prices (sudden large swings)
        3. Stalling (same price repeated 3+ times)

    Returns a warning string if suspicious, else None.
    """
    # 1. Lowball detection
    if reference_price > 0 and current_price / reference_price < LOWBALL_THRESHOLD:
        return (
            f"ADVERSARIAL: Offer {current_price} is only "
            f"{(current_price/reference_price)*100:.0f}% of reference {reference_price}. "
            f"Possible aggressive lowballing."
        )

    # 2. Price oscillation detection
    if len(round_history) >= 3:
        recent_prices = [r.get("price", 0) for r in round_history[-3:]]
        if len(recent_prices) == 3:
            avg = sum(recent_prices) / 3
            if avg > 0:
                max_deviation = max(abs(p - avg) / avg for p in recent_prices)
                if max_deviation > 0.20:
                    return (
                        f"ADVERSARIAL: Large price oscillation in last 3 rounds. "
                        f"Prices: {recent_prices}. Possible manipulation."
                    )

    # 3. Stalling detection
    if len(round_history) >= 3:
        recent_prices = [r.get("price", 0) for r in round_history[-3:]]
        if len(set(recent_prices)) == 1:
            return (
                f"ADVERSARIAL: Same price {recent_prices[0]} repeated "
                f"for 3 consecutive rounds. Possible stalling tactic."
            )

    return None


def validate_concession_rate(
    old_price: float,
    new_price: float,
    role: str,
) -> None:
    """Ensure the agent doesn't concede more than the allowed rate per round."""
    if old_price == 0:
        return

    if role == "buyer":
        concession = (new_price - old_price) / old_price
    else:
        concession = (old_price - new_price) / old_price

    if concession > MAX_CONCESSION_RATE:
        raise GuardrailViolation(
            f"Concession rate {concession*100:.1f}% exceeds maximum "
            f"{MAX_CONCESSION_RATE*100:.0f}% per round. "
            f"Old: {old_price} → New: {new_price}"
        )


# ────────────────────────────────────────────────────────────────────
# Full Pre-Negotiation Validation
# ────────────────────────────────────────────────────────────────────

def run_pre_negotiation_checks(
    budget: float,
    market_price: float = 0.0,
) -> dict:
    """
    Run all pre-negotiation guardrail checks.

    Returns a dict with:
        - passed: bool
        - warnings: list of warning strings
        - high_value: bool — whether extra approval is needed
    """
    warnings = []

    # Budget validation
    validate_budget(budget)

    # High-value flag
    high_value = requires_high_value_approval(budget)
    if high_value:
        warnings.append(
            f"Deal exceeds {HIGH_VALUE_APPROVAL_THRESHOLD} — "
            f"additional confirmation may be required."
        )

    # Market sanity check
    if market_price > 0 and budget > market_price * UPPER_FLAG:
        warnings.append(
            f"Budget {budget} is over {UPPER_FLAG}× market price {market_price}. "
            f"Are you sure?"
        )

    return {
        "passed": True,
        "warnings": warnings,
        "high_value": high_value,
    }
