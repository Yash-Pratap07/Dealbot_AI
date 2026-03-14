"""Safety and Fraud Detection for DealBot AI."""

# Fraud thresholds (per spec)
_UPPER_FLAG   = 2.0   # price > 2× market → FLAG
_LOWER_FLAG   = 0.30  # price < 30% of market → FLAG (suspiciously cheap)
_GAP_FLAG     = 5.0   # seller > 5× buyer → extreme mismatch


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

    if seller_price > market_price * _UPPER_FLAG:
        return (
            f"FLAG: Seller ${seller_price:,.2f} is over {_UPPER_FLAG}× "
            f"market price ${market_price:,.2f} — possible manipulation"
        )
    if buyer_price > market_price * _UPPER_FLAG:
        return (
            f"FLAG: Buyer offer ${buyer_price:,.2f} is over {_UPPER_FLAG}× "
            f"market price ${market_price:,.2f} — suspicious wallet"
        )
    if seller_price < market_price * _LOWER_FLAG:
        return (
            f"FLAG: Seller ${seller_price:,.2f} is below 30% of market "
            f"${market_price:,.2f} — suspicious listing"
        )
    if buyer_price > 0 and seller_price / max(buyer_price, 0.01) > _GAP_FLAG:
        return (
            f"FLAG: Extreme gap — seller ${seller_price:,.2f} "
            f"vs buyer ${buyer_price:,.2f}"
        )
    return None


def is_safe(content: str) -> bool:
    """Legacy content safety check."""
    return bool(content and content.strip())
