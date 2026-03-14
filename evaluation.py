"""
Evaluator AI — checks if a negotiated price is fair.
Returns ACCEPT or NEGOTIATE (per spec).

Config: marketPrice, buyerOffer, sellerPrice, dealConfidence
"""

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
