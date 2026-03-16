"""
DEALBOT — Agent Guardrails
============================

Safety constraints enforced on every DealAgent instance.
Per dealbot_architecture.md §4.2 (Trust & Safety Design):

    - Budget enforcement (hard-coded max per agent)
    - Time-based abort (negotiations > 24 hours)
    - Adversarial pattern detection (aggressive lowballing)
    - Counterparty whitelist validation
    - Mandate enforcement (agents never exceed user-set boundaries)
"""

import time
from typing import Optional


# ---------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------

MAX_BUDGET_HARD_LIMIT = 100_000.0     # WUSD — absolute ceiling for any single deal
MAX_NEGOTIATION_HOURS = 24            # Auto-abort after this duration
MIN_PRICE_FLOOR = 1.0                 # No deal below 1 WUSD
MAX_CONCESSION_RATE = 0.25            # Agent cannot concede more than 25% per round
LOWBALL_THRESHOLD = 0.3               # Flag if offer is < 30% of budget/asking price
HIGH_VALUE_APPROVAL_THRESHOLD = 10_000.0  # Require extra confirmation above 10K WUSD


class GuardrailViolation(Exception):
    """Raised when a negotiation violates a safety guardrail."""
    pass


# ---------------------------------------------------------------
# Budget Guardrails
# ---------------------------------------------------------------

def validate_budget(budget: float) -> None:
    """Ensure budget is within acceptable bounds."""
    if budget <= 0:
        raise GuardrailViolation(
            f"Budget must be positive, got {budget} WUSD"
        )
    if budget > MAX_BUDGET_HARD_LIMIT:
        raise GuardrailViolation(
            f"Budget {budget} WUSD exceeds hard limit of {MAX_BUDGET_HARD_LIMIT} WUSD"
        )


def validate_price_bounds(price: float, max_budget: float, role: str) -> None:
    """Ensure a proposed price doesn't violate the agent's mandate."""
    if price < MIN_PRICE_FLOOR:
        raise GuardrailViolation(
            f"Price {price} WUSD below minimum floor of {MIN_PRICE_FLOOR} WUSD"
        )

    if role == "buyer" and price > max_budget:
        raise GuardrailViolation(
            f"Buyer price {price} WUSD exceeds max budget of {max_budget} WUSD"
        )

    if role == "seller" and price < max_budget:
        raise GuardrailViolation(
            f"Seller price {price} WUSD below minimum floor of {max_budget} WUSD"
        )


def requires_high_value_approval(price: float) -> bool:
    """Check if the deal exceeds the high-value approval threshold (>10K WUSD)."""
    return price >= HIGH_VALUE_APPROVAL_THRESHOLD


# ---------------------------------------------------------------
# Time-Based Guardrails
# ---------------------------------------------------------------

def validate_negotiation_duration(start_time: float) -> None:
    """Auto-abort if negotiation exceeds the maximum allowed duration."""
    elapsed_hours = (time.time() - start_time) / 3600
    if elapsed_hours > MAX_NEGOTIATION_HOURS:
        raise GuardrailViolation(
            f"Negotiation exceeded {MAX_NEGOTIATION_HOURS}-hour time limit "
            f"({elapsed_hours:.1f} hours elapsed). Auto-aborting."
        )


# ---------------------------------------------------------------
# Adversarial Detection
# ---------------------------------------------------------------

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
            f"ADVERSARIAL: Offer {current_price} WUSD is only "
            f"{(current_price/reference_price)*100:.0f}% of reference {reference_price} WUSD. "
            f"Possible aggressive lowballing."
        )

    # 2. Price oscillation detection
    if len(round_history) >= 3:
        recent_prices = [r.get("price", 0) for r in round_history[-3:]]
        if len(recent_prices) == 3:
            # Check if prices are swinging wildly (>20% variance)
            avg = sum(recent_prices) / 3
            if avg > 0:
                max_deviation = max(abs(p - avg) / avg for p in recent_prices)
                if max_deviation > 0.20:
                    return (
                        f"ADVERSARIAL: Large price oscillation detected in last 3 rounds. "
                        f"Prices: {recent_prices}. Possible manipulation."
                    )

    # 3. Stalling detection
    if len(round_history) >= 3:
        recent_prices = [r.get("price", 0) for r in round_history[-3:]]
        if len(set(recent_prices)) == 1:
            return (
                f"ADVERSARIAL: Same price {recent_prices[0]} WUSD repeated "
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
        # Buyer concedes by increasing price
        concession = (new_price - old_price) / old_price
    else:
        # Seller concedes by decreasing price
        concession = (old_price - new_price) / old_price

    if concession > MAX_CONCESSION_RATE:
        raise GuardrailViolation(
            f"Concession rate {concession*100:.1f}% exceeds maximum "
            f"{MAX_CONCESSION_RATE*100:.0f}% per round. "
            f"Old: {old_price} → New: {new_price} WUSD"
        )


# ---------------------------------------------------------------
# Counterparty Whitelist
# ---------------------------------------------------------------

# In production, this would query WeilChain verified identities
_WHITELIST = {
    "0x4b2e_designer",
    "0x4b2e_design_studio",
    "0x9c1a_bulk_supplier",
}


def validate_counterparty(wallet: str, strict: bool = False) -> bool:
    """
    Check if a counterparty is on the verified whitelist.
    In non-strict mode, returns False for unknown wallets (warning only).
    In strict mode, raises GuardrailViolation.
    """
    is_whitelisted = wallet in _WHITELIST

    if not is_whitelisted and strict:
        raise GuardrailViolation(
            f"Counterparty {wallet} is not on the verified whitelist. "
            f"Strict mode is enabled — negotiation blocked."
        )

    return is_whitelisted


# ---------------------------------------------------------------
# Full Pre-Negotiation Validation
# ---------------------------------------------------------------

def run_pre_negotiation_checks(
    budget: float,
    counterparty_wallet: str,
    strict_whitelist: bool = False,
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

    # Whitelist check
    if not validate_counterparty(counterparty_wallet, strict=strict_whitelist):
        warnings.append(
            f"Counterparty {counterparty_wallet} is not verified. Proceed with caution."
        )

    # High-value flag
    high_value = requires_high_value_approval(budget)
    if high_value:
        warnings.append(
            f"Deal exceeds {HIGH_VALUE_APPROVAL_THRESHOLD} WUSD — "
            f"biometric/2FA confirmation may be required."
        )

    return {
        "passed": True,
        "warnings": warnings,
        "high_value": high_value,
    }
