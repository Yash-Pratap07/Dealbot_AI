"""
DEALBOT — Intent Parser
========================

Extracts structured negotiation parameters from natural language prompts.
Converts user intent into DealAgent configuration.

Example:
    "I need a logo designer, budget $500, delivery in 7 days"
    → {"service": "logo_design", "budget": 500.0, "days": 7, "w_price": 0.7, "w_time": 0.3}
"""

import re
from typing import Optional


# ---------------------------------------------------------------
# Keyword → service category mapping
# ---------------------------------------------------------------

SERVICE_KEYWORDS = {
    "logo": "freelance_logo_design",
    "graphic design": "freelance_logo_design",
    "branding": "freelance_logo_design",
    "web": "web_development",
    "website": "web_development",
    "frontend": "web_development",
    "backend": "web_development",
    "fullstack": "web_development",
    "copywriting": "copywriting_landing_page",
    "copy": "copywriting_landing_page",
    "landing page": "copywriting_landing_page",
    "content": "copywriting_landing_page",
    "smart contract": "smart_contract_audit",
    "audit": "smart_contract_audit",
    "solidity": "smart_contract_audit",
    "security review": "smart_contract_audit",
}

# Default weight presets based on keywords
WEIGHT_PRESETS = {
    "cheap": (0.9, 0.1),        # "find me the cheapest..."
    "fast": (0.3, 0.7),         # "I need it urgently..."
    "urgent": (0.2, 0.8),       # "ASAP..."
    "quality": (0.6, 0.4),      # "best quality..."
    "balanced": (0.5, 0.5),     # default
}


def parse_negotiation_intent(prompt: str) -> dict:
    """
    Parse a natural language negotiation request into structured parameters.

    Parameters
    ----------
    prompt : str — user's natural language request via Icarus

    Returns
    -------
    dict with keys:
        - service       : str — mapped service category for MCP lookup
        - budget        : float — maximum budget in WUSD
        - days          : int — delivery timeline in days
        - w_price       : float — price weight
        - w_time        : float — time weight
        - deliverables  : list[str] — extracted deliverable items
        - raw_prompt    : str — original user input
    """
    prompt_lower = prompt.lower()

    # --- 1. Extract service category ---
    service = _extract_service(prompt_lower)

    # --- 2. Extract budget ---
    budget = _extract_budget(prompt_lower)

    # --- 3. Extract timeline ---
    days = _extract_timeline(prompt_lower)

    # --- 4. Determine weight preferences ---
    w_price, w_time = _extract_weights(prompt_lower)

    # --- 5. Extract deliverables ---
    deliverables = _extract_deliverables(prompt_lower)

    return {
        "service": service,
        "budget": budget,
        "days": days,
        "w_price": round(w_price, 2),
        "w_time": round(w_time, 2),
        "deliverables": deliverables,
        "raw_prompt": prompt,
    }


def _extract_service(text: str) -> str:
    """Match keywords to service categories."""
    for keyword, category in SERVICE_KEYWORDS.items():
        if keyword in text:
            return category
    return "general_service"


def _extract_budget(text: str) -> float:
    """
    Extract budget from patterns like:
        - "budget $500", "budget 500", "$500"
        - "max 800 WUSD", "up to 1000"
        - "500-800" (takes the max)
    """
    # Pattern: "$500" or "500 WUSD" or "500 dollars"
    patterns = [
        r'\$\s*([\d,]+(?:\.\d{2})?)',                    # $500 or $1,000.00
        r'([\d,]+(?:\.\d{2})?)\s*(?:wusd|usd|dollars?)', # 500 WUSD
        r'budget\s*(?:of\s*)?(?:\$)?\s*([\d,]+(?:\.\d{2})?)',  # budget 500
        r'(?:max|maximum|up\s*to|under|below)\s*(?:\$)?\s*([\d,]+(?:\.\d{2})?)',  # max 500
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', ''))

    # Range pattern: "500-800" → take the max
    range_match = re.search(r'([\d,]+)\s*[-–to]+\s*([\d,]+)', text)
    if range_match:
        return float(range_match.group(2).replace(',', ''))

    return 500.0  # Default budget


def _extract_timeline(text: str) -> int:
    """
    Extract delivery timeline from patterns like:
        - "7 days", "2 weeks", "1 month"
        - "by next week", "ASAP"
    """
    # Days pattern
    days_match = re.search(r'(\d+)\s*(?:day|days)', text)
    if days_match:
        return int(days_match.group(1))

    # Weeks pattern
    weeks_match = re.search(r'(\d+)\s*(?:week|weeks)', text)
    if weeks_match:
        return int(weeks_match.group(1)) * 7

    # Month pattern
    month_match = re.search(r'(\d+)\s*(?:month|months)', text)
    if month_match:
        return int(month_match.group(1)) * 30

    # Keyword-based
    if any(word in text for word in ["asap", "urgent", "rush", "immediately"]):
        return 3
    if "next week" in text:
        return 7

    return 7  # Default: 1 week


def _extract_weights(text: str) -> tuple:
    """Determine price/time weights from keyword cues."""
    for keyword, (w_p, w_t) in WEIGHT_PRESETS.items():
        if keyword in text:
            return (w_p, w_t)

    # Default: slightly price-favoring
    return (0.7, 0.3)


def _extract_deliverables(text: str) -> list:
    """Extract deliverable items from the prompt."""
    deliverables = []

    # Look for "with X, Y, and Z" or "including X, Y"
    include_match = re.search(
        r'(?:with|including|include|want|need)\s+(.+?)(?:\.|$)',
        text
    )
    if include_match:
        items_text = include_match.group(1)
        # Split on commas and "and"
        items = re.split(r',\s*|\s+and\s+', items_text)
        deliverables = [item.strip() for item in items if len(item.strip()) > 2]

    # Look for "N revisions" or "N rounds"
    revision_match = re.search(r'(\d+)\s*(?:revision|round)', text)
    if revision_match:
        deliverables.append(f"{revision_match.group(1)} revision rounds")

    return deliverables or ["Standard deliverables"]
