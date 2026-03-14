import os
import asyncio
import random
import re
import logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("llm_router")


def _extract_value(prompt: str, label: str):
    match = re.search(rf"{label}\s*:\s*(\d+\.?\d*)", prompt, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _last_history_offer(prompt: str, role: str):
    matches = re.findall(rf"{role}:\s*(\d+\.?\d*)", prompt, re.IGNORECASE)
    return float(matches[-1]) if matches else None


def _mock_offer(prompt: str) -> str:
    """Fallback mock offer when no real LLM key is configured."""
    lower_prompt = prompt.lower()

    if "you are a strategic buyer" in lower_prompt:
        max_budget = _extract_value(prompt, "Maximum budget") or 1000
        last_seller = _last_history_offer(prompt, "Seller")

        if last_seller is not None:
            lower_bound = max(max_budget * 0.55, min(last_seller * 0.82, max_budget * 0.9))
            upper_bound = min(max_budget, max(max_budget * 0.7, last_seller * 0.92))
        else:
            lower_bound = max_budget * 0.55
            upper_bound = max_budget * 0.75

        if upper_bound < lower_bound:
            upper_bound = lower_bound
        offer = random.uniform(lower_bound, upper_bound)

    elif "you are a seller" in lower_prompt:
        min_price = _extract_value(prompt, "Minimum acceptable price") or 500
        last_buyer = _last_history_offer(prompt, "Buyer")

        if last_buyer is not None:
            lower_bound = max(min_price, last_buyer * 1.05)
            upper_bound = max(lower_bound, min(min_price * 1.8, last_buyer * 1.22))
        else:
            lower_bound = min_price * 1.35
            upper_bound = min_price * 1.8

        if upper_bound < lower_bound:
            upper_bound = lower_bound
        offer = random.uniform(lower_bound, upper_bound)

    else:
        offer = random.uniform(600, 900)

    return str(round(offer, 2))


def _extract_price_from_response(text: str) -> str:
    """Pull a numeric price from an LLM response string."""
    # Look for $price or standalone numbers
    m = re.search(r'\$?([\d,]+\.?\d*)', text)
    if m:
        return m.group(1).replace(',', '')
    return text.strip()


# ── Real Gemini via google-generativeai ────────────────────────────────────────

async def call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key.startswith("YOUR_"):
        return _mock_offer(prompt)
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = await asyncio.to_thread(
            lambda: model.generate_content(prompt + "\n\nRespond with ONLY a numeric price, no other text.")
        )
        return _extract_price_from_response(resp.text)
    except Exception as e:
        log.warning("Gemini API failed (%s), using mock", e)
        return _mock_offer(prompt)


# ── Real GPT via openai ───────────────────────────────────────────────────────

async def call_gpt(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key.startswith("YOUR_") or api_key == "sk-abcdef1234567890abcdef1234567890abcdef12":
        return _mock_offer(prompt)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a price negotiation agent. Respond with ONLY a numeric price."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=20,
                temperature=0.7,
            )
        )
        return _extract_price_from_response(resp.choices[0].message.content or "")
    except Exception as e:
        log.warning("GPT API failed (%s), using mock", e)
        return _mock_offer(prompt)


# ── Real Claude via anthropic ─────────────────────────────────────────────────

async def call_claude(prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("YOUR_"):
        return _mock_offer(prompt)
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        resp = await asyncio.to_thread(
            lambda: client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=20,
                messages=[{"role": "user", "content": prompt + "\n\nRespond with ONLY a numeric price, no other text."}],
            )
        )
        text = resp.content[0].text if resp.content else ""
        return _extract_price_from_response(text)
    except Exception as e:
        log.warning("Claude API failed (%s), using mock", e)
        return _mock_offer(prompt)
