"""Quick API key verification script — run with: py verify_apis.py"""
from dotenv import load_dotenv
load_dotenv()
import os
import requests

print("\n=== DealBot AI — API Key Verification ===\n")

# ── 1. SerpAPI ────────────────────────────────────────────────────────────────
try:
    r = requests.get("https://serpapi.com/search.json", params={
        "q": "iphone 16", "engine": "google_shopping",
        "api_key": os.getenv("SERPAPI_KEY"), "num": 2
    }, timeout=12)
    d = r.json()
    if "error" in d:
        print(f"  SerpAPI       FAIL  -> {d['error']}")
    else:
        results = d.get("shopping_results", d.get("organic_results", []))
        print(f"  SerpAPI       OK    -> {len(results)} results  |  first: {results[0].get('title','?')[:50] if results else 'none'}")
except Exception as e:
    print(f"  SerpAPI       ERROR -> {e}")

# ── 2. Google CSE ─────────────────────────────────────────────────────────────
try:
    r = requests.get("https://www.googleapis.com/customsearch/v1", params={
        "q": "iphone 16 price buy",
        "key": os.getenv("GOOGLE_CSE_KEY"),
        "cx":  os.getenv("GOOGLE_CSE_ID"),
        "num": 2
    }, timeout=12)
    d = r.json()
    if "error" in d:
        msg = d["error"].get("message", str(d["error"]))
        print(f"  Google CSE    FAIL  -> {msg}")
    else:
        items = d.get("items", [])
        print(f"  Google CSE    OK    -> {len(items)} results  |  first: {items[0].get('title','?')[:50] if items else 'none'}")
except Exception as e:
    print(f"  Google CSE    ERROR -> {e}")

# ── 3. DuckDuckGo (no key) ────────────────────────────────────────────────────
try:
    r = requests.post("https://html.duckduckgo.com/html/",
        data={"q": "iphone 16 price"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0"},
        timeout=12)
    if r.status_code == 200 and len(r.text) > 500:
        print(f"  DuckDuckGo    OK    -> reachable, {len(r.text)} bytes")
    else:
        print(f"  DuckDuckGo    FAIL  -> status {r.status_code}")
except Exception as e:
    print(f"  DuckDuckGo    ERROR -> {e}")

# ── 4. Google OAuth Client ────────────────────────────────────────────────────
cid = os.getenv("GOOGLE_CLIENT_ID", "")
print(f"  Google OAuth  {'OK    -> ' + cid[:30] + '...' if cid else 'MISSING'}")

# ── 5. LLM Keys (existence check only — no free test endpoint) ───────────────
for name, env in [("OpenAI", "OPENAI_API_KEY"), ("Anthropic", "ANTHROPIC_API_KEY"),
                  ("Gemini", "GEMINI_API_KEY"), ("Grok", "GROK_API_KEY")]:
    v = os.getenv(env, "")
    print(f"  {name:<14}{'SET   -> ' + v[:14] + '...' if v else 'MISSING'}")

print()
