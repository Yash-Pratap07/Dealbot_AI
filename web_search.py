"""
DealBot AI  –  Real Web Search Engine
======================================
Multi-tier product search:

  Tier 1 » SerpAPI          (env: SERPAPI_KEY)         100 free searches/month
  Tier 2 » Google CSE       (env: GOOGLE_CSE_KEY +     100 free searches/day
                                   GOOGLE_CSE_ID)
  Tier 3 » DuckDuckGo HTML  (no key needed)            always available
  Tier 4 » Direct scrapers  (no key needed)            Amazon · Flipkart ·
                                                        BestBuy · Croma

How to get free keys
─────────────────────
  SerpAPI:    https://serpapi.com  → Sign up → Dashboard → API Key
  Google CSE: https://programmablesearch.google.com
                → Create search engine (set "Search the entire web")
                → Copy "Search engine ID"
              https://console.cloud.google.com
                → Enable "Custom Search JSON API" → Create API key
  Both have generous free tiers with no credit card required.

Put keys in  .env  (copy .env.example):
  SERPAPI_KEY=<your_serpapi_key>
  GOOGLE_CSE_KEY=<your_google_api_key>
  GOOGLE_CSE_ID=<your_cx_id>
"""

from __future__ import annotations

import os
import re
import uuid
import time
import random
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import quote_plus, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from bs4 import BeautifulSoup
    _BS4 = True
except ImportError:
    _BS4 = False

log = logging.getLogger(__name__)

# ─── HTTP helpers ──────────────────────────────────────────────────────────────

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]


def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h: Dict[str, str] = {
        "User-Agent":      random.choice(_UA_POOL),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT":             "1",
        "Connection":      "keep-alive",
    }
    if extra:
        h.update(extra)
    return h


def _new_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    return s


# ─── Price / Rating parsers ────────────────────────────────────────────────────

_PRICE_RX: List[Tuple[str, str]] = [
    (r"[₹]\s*([\d,]+(?:\.\d{1,2})?)",              "INR"),
    (r"Rs\.?\s*([\d,]+(?:\.\d{1,2})?)",             "INR"),
    (r"\bINR\s*([\d,]+(?:\.\d{1,2})?)",             "INR"),
    (r"\$\s*([\d,]+(?:\.\d{1,2})?)",                "USD"),
    (r"\bUSD\s*([\d,]+(?:\.\d{1,2})?)",             "USD"),
    (r"€\s*([\d,]+(?:\.\d{1,2})?)",                 "EUR"),
    (r"£\s*([\d,]+(?:\.\d{1,2})?)",                 "GBP"),
]


def _parse_price(text: str) -> Tuple[Optional[float], str]:
    """Return (price_float, currency_code) or (None, 'USD')."""
    clean = text.replace("\u00a0", " ").replace(",", "")
    for pattern, cur in _PRICE_RX:
        m = re.search(pattern, clean)
        if m:
            try:
                v = float(m.group(1).replace(",", ""))
                if v > 0:
                    return v, cur
            except ValueError:
                pass
    return None, "USD"


def _parse_rating(text: str) -> Optional[float]:
    m = re.search(r"(\d\.?\d?)\s*(?:out\s+of\s+5|/5|★|stars?)", text, re.I)
    if m:
        try:
            v = float(m.group(1))
            return v if 0 <= v <= 5 else None
        except ValueError:
            pass
    return None


def _parse_review_count(text: str) -> int:
    m = re.search(r"([\d,]+)\s*(?:rating|review|customer|vote)", text, re.I)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return 0


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.removeprefix("www.")
    except Exception:
        return ""


_DOMAIN_SELLERS: Dict[str, str] = {
    "amazon.in":          "Amazon India",
    "amazon.com":         "Amazon US",
    "flipkart.com":       "Flipkart",
    "croma.com":          "Croma",
    "reliancedigital.in": "Reliance Digital",
    "bestbuy.com":        "Best Buy",
    "newegg.com":         "Newegg",
    "apple.com":          "Apple Store",
    "myntra.com":         "Myntra",
    "snapdeal.com":       "Snapdeal",
    "ebay.com":           "eBay",
    "ebay.in":            "eBay India",
    "tatacliq.com":       "Tata CLiQ",
    "samsung.com":        "Samsung Shop",
}


def _seller_from_url(url: str) -> str:
    d = _extract_domain(url)
    for key, name in _DOMAIN_SELLERS.items():
        if key in d:
            return name
    return d.split(".")[0].capitalize() if d else "Online Store"


# ─── Category mapper ──────────────────────────────────────────────────────────

_CAT_RULES: List[Tuple[List[str], str, str]] = [
    (["gaming laptop", "rog", "legion", "omen", "alienware", "nitro", "rtx laptop", "gaming notebook"],
     "Gaming Laptops", "🎮"),
    (["laptop", "notebook", "macbook", "thinkpad", "xps", "chromebook", "surface pro", "ultrabook"],
     "Laptops", "💻"),
    (["iphone", "galaxy", "pixel", "oneplus", "poco", "redmi", "realme", "vivo oppo", "smartphone", "phone", "mobile"],
     "Smartphones", "📱"),
    (["headphone", "earphone", "earbuds", "airpods", "buds", "wh-1000", "sony wf", "over-ear", "in-ear", "tws"],
     "Headphones", "🎧"),
    (["speaker", "soundbar", "bluetooth speaker", "jbl", "harman", "bose soundlink"],
     "Speakers", "🔊"),
    (["dslr", "mirrorless", "canon eos", "nikon", "sony alpha", "action cam", "gopro", "camera"],
     "Cameras", "📷"),
    (["tv", "television", "oled tv", "qled", "led tv", "smart tv", "4k tv"],
     "TV & Display", "📺"),
    (["tablet", "ipad", "android tablet", "surface go"],
     "Tablets", "📲"),
    (["rtx 40", "rtx 50", "rx 7900", "radeon rx", "geforce", "gpu", "graphics card"],
     "GPU / Components", "🖥️"),
    (["drone", "dji", "mavic", "fpv", "quadcopter"],
     "Drones", "🚁"),
    (["smartwatch", "apple watch", "galaxy watch", "fitbit", "garmin"],
     "Smartwatches", "⌚"),
    (["shoe", "sneaker", "nike", "adidas", "jordan", "running shoe"],
     "Footwear", "👟"),
    (["vacuum", "dyson", "washing machine", "refrigerator", "fridge", "microwave"],
     "Home Appliances", "🏠"),
    (["playstation", "ps5", "ps6", "xbox", "nintendo switch"],
     "Gaming Consoles", "🕹️"),
]


def _categorize(title: str) -> Tuple[str, str]:
    t = title.lower()
    for keywords, cat, emoji in _CAT_RULES:
        if any(kw in t for kw in keywords):
            return cat, emoji
    return "Electronics", "📦"


# ─── WebProduct ───────────────────────────────────────────────────────────────

@dataclass
class WebProduct:
    title:        str
    price:        Optional[float]    = None
    currency:     str                = "USD"
    rating:       Optional[float]    = None
    review_count: int                = 0
    source:       str                = ""
    url:          str                = ""
    image:        str                = ""
    snippet:      str                = ""
    in_stock:     bool               = True
    found_via:    str                = ""
    category:     str                = ""
    emoji:        str                = ""

    def __post_init__(self) -> None:
        if not self.source and self.url:
            self.source = _seller_from_url(self.url)
        if not self.category:
            self.category, self.emoji = _categorize(self.title)

    def to_dict(self) -> dict:
        return {
            "title":        self.title,
            "price":        self.price,
            "currency":     self.currency,
            "rating":       self.rating,
            "review_count": self.review_count,
            "source":       self.source,
            "url":          self.url,
            "snippet":      self.snippet[:200] if self.snippet else "",
            "in_stock":     self.in_stock,
            "found_via":    self.found_via,
            "category":     self.category,
            "emoji":        self.emoji,
        }


# ─── AI Query Generator ────────────────────────────────────────────────────────

class QueryGenerator:
    """
    Generates multiple targeted search queries from a natural-language shopping request.
    More queries = more coverage = better results.
    """

    _TEMPLATES = [
        "{q} buy online best price",
        "{q} price 2025",
        "best {q} deals discount",
        "{q} review specifications",
    ]

    _INDIA_SUFFIXES  = ["india", "₹", "inr", "flipkart", "amazon india", "croma", "reliance digital"]
    _BUDGET_TEMPLATE = "{q} under {budget}"

    def generate(
        self,
        query: str,
        category: str = "general",
        budget: Optional[float] = None,
        currency: str = "USD",
        limit: int = 4,
    ) -> List[str]:
        q = query.strip()
        queries: List[str] = [q]

        # If budget present, add budget-constrained version
        if budget:
            sym = "₹" if currency == "INR" else "$"
            queries.append(f"{q} under {sym}{int(budget):,}")

        # Add templates
        for tmpl in self._TEMPLATES[:limit - len(queries)]:
            queries.append(tmpl.format(q=q, budget=budget or ""))

        # If India-context query, add India-specific variant
        q_lower = q.lower()
        if any(s in q_lower for s in self._INDIA_SUFFIXES):
            queries.append(f"{q} flipkart amazon.in croma")

        return queries[:limit]


# ─── Tier 1: SerpAPI ──────────────────────────────────────────────────────────

class SerpAPISearcher:
    """
    Uses SerpAPI to get Google Shopping + organic results.
    Free tier: 100 searches/month, no credit card needed.
    Docs: https://serpapi.com/shopping-results
    """
    BASE = "https://serpapi.com/search.json"

    def __init__(self) -> None:
        self.api_key = os.getenv("SERPAPI_KEY", "").strip()

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 10) -> List[WebProduct]:
        if not self.is_available():
            return []
        params = {
            "q":       query,
            "engine":  "google_shopping",
            "api_key": self.api_key,
            "num":     limit,
            "hl":      "en",
        }
        try:
            r = requests.get(self.BASE, params=params, timeout=12)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            log.warning("SerpAPI error: %s", exc)
            return []

        products: List[WebProduct] = []

        # ── Shopping results (structured, have price) ──────────────────────
        for item in data.get("shopping_results", []):
            price, cur = _parse_price(str(item.get("price", "")))
            ratingv = item.get("rating")
            products.append(WebProduct(
                title        = item.get("title", ""),
                price        = price,
                currency     = cur,
                rating       = float(ratingv) if ratingv else None,
                review_count = int(str(item.get("reviews", "0")).replace(",", "") or 0),
                source       = item.get("source", "") or _seller_from_url(item.get("link", "")),
                url          = item.get("link", ""),
                image        = item.get("thumbnail", ""),
                snippet      = item.get("snippet", ""),
                found_via    = "serpapi_shopping",
            ))

        # ── Organic results fallback ───────────────────────────────────────
        if len(products) < limit // 2:
            for item in data.get("organic_results", [])[:limit]:
                snippet = item.get("snippet", "")
                price, cur = _parse_price(snippet)
                products.append(WebProduct(
                    title     = item.get("title", ""),
                    price     = price,
                    currency  = cur,
                    source    = _seller_from_url(item.get("link", "")),
                    url       = item.get("link", ""),
                    snippet   = snippet,
                    found_via = "serpapi_organic",
                ))

        return products[:limit]


# ─── Tier 2: Google Custom Search ─────────────────────────────────────────────

class GoogleCSESearcher:
    """
    Google Custom Search JSON API.
    Free: 100 queries/day.
    Setup: https://programmablesearch.google.com  +  https://console.cloud.google.com
    """
    BASE = "https://www.googleapis.com/customsearch/v1"

    def __init__(self) -> None:
        self.api_key = os.getenv("GOOGLE_CSE_KEY", "").strip()
        self.cx      = os.getenv("GOOGLE_CSE_ID",  "").strip()

    def is_available(self) -> bool:
        return bool(self.api_key and self.cx)

    def search(self, query: str, limit: int = 10) -> List[WebProduct]:
        if not self.is_available():
            return []
        params = {
            "q":   query + " buy price",
            "key": self.api_key,
            "cx":  self.cx,
            "num": min(limit, 10),
        }
        try:
            r = requests.get(self.BASE, params=params, timeout=12)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            log.warning("Google CSE error: %s", exc)
            return []

        products: List[WebProduct] = []
        for item in data.get("items", []):
            snippet = item.get("snippet", "")
            meta = " ".join(
                v for v in (item.get("pagemap", {}).get("metatags", [{}])[0].get("og:description", ""),) if v
            )
            price, cur = _parse_price(snippet + " " + meta)
            rating_text = item.get("pagemap", {}).get("aggregaterating", [{}])
            rating = None
            if rating_text:
                rating = _parse_rating(str(rating_text[0].get("ratingvalue", "")))

            products.append(WebProduct(
                title     = item.get("title", ""),
                price     = price,
                currency  = cur,
                rating    = rating,
                source    = _seller_from_url(item.get("link", "")),
                url       = item.get("link", ""),
                snippet   = snippet,
                found_via = "google_cse",
            ))

        return products[:limit]


# ─── Tier 3: DuckDuckGo (no key) ──────────────────────────────────────────────

class DuckDuckGoSearcher:
    """
    Scrapes DuckDuckGo's HTML search endpoint.
    No API key required — always available as fallback.
    """
    URL = "https://html.duckduckgo.com/html/"

    def is_available(self) -> bool:
        return _BS4

    def search(self, query: str, limit: int = 10) -> List[WebProduct]:
        if not _BS4:
            log.info("DuckDuckGoSearcher: beautifulsoup4 not installed – skipped")
            return []
        try:
            sess = _new_session()
            r = sess.post(
                self.URL,
                data={"q": query + " price buy"},
                headers=_headers({"Content-Type": "application/x-www-form-urlencoded"}),
                timeout=12,
                allow_redirects=True,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as exc:
            log.warning("DuckDuckGo error: %s", exc)
            return []

        products: List[WebProduct] = []
        for result in soup.select(".result__body")[:limit]:
            title_el   = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            if not title_el:
                continue
            title   = title_el.get_text(strip=True)
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            url     = title_el.get("href", "")
            price, cur = _parse_price(snippet + " " + title)
            products.append(WebProduct(
                title     = title,
                price     = price,
                currency  = cur,
                source    = _seller_from_url(url),
                url       = url,
                snippet   = snippet,
                found_via = "duckduckgo",
            ))
        return products


# ─── Tier 4a: Amazon Scraper ──────────────────────────────────────────────────

class AmazonScraper:
    """
    Scrapes Amazon search results using BeautifulSoup.
    Works best without bot-detection (may fail without proxies).
    Implements polite delays and realistic headers.
    """

    def _search_url(self, query: str, region: str = "in") -> str:
        base = f"https://www.amazon.{region}/s"
        return f"{base}?k={quote_plus(query)}&ref=nb_sb_noss"

    def _scrape(self, url: str, limit: int) -> List[WebProduct]:
        if not _BS4:
            return []
        try:
            sess = _new_session()
            r = sess.get(
                url,
                headers=_headers({
                    "Accept":          "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-IN,en;q=0.9",
                    "Referer":         "https://www.amazon.in/",
                }),
                timeout=14,
                allow_redirects=True,
            )
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as exc:
            log.warning("Amazon scrape error: %s", exc)
            return []

        products: List[WebProduct] = []
        items = soup.select('[data-component-type="s-search-result"]')[:limit]
        if not items:
            # Fallback selector
            items = soup.select(".s-result-item[data-asin]")[:limit]

        for item in items:
            asin = item.get("data-asin", "")
            if not asin:
                continue

            # Title
            title_el = item.select_one("h2 a span") or item.select_one(".a-size-medium.a-color-base")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # Price — whole + fraction
            whole    = item.select_one(".a-price-whole")
            fraction = item.select_one(".a-price-fraction")
            if whole:
                price_text = whole.get_text(strip=True).replace(",", "").rstrip(".")
                if fraction:
                    price_text += "." + fraction.get_text(strip=True)
                try:
                    price = float(price_text)
                    cur   = "INR" if "amazon.in" in url else "USD"
                except ValueError:
                    price, cur = None, "USD"
            else:
                price_text = item.get_text(" ")
                price, cur = _parse_price(price_text)

            # Rating
            rating_el = item.select_one(".a-icon-alt")
            rating = _parse_rating(rating_el.get_text()) if rating_el else None

            # Review count
            review_el = item.select_one(".a-size-base.s-underline-text")
            rc = _parse_review_count(review_el.get_text()) if review_el else 0

            # Link
            link_el = item.select_one("h2 a[href]")
            path    = link_el["href"] if link_el else f"/dp/{asin}"
            domain  = "amazon.in" if "amazon.in" in url else "amazon.com"
            full_url = f"https://www.{domain}{path.split('?')[0]}"

            # Image
            img_el = item.select_one(".s-image")
            image  = img_el["src"] if img_el else ""

            products.append(WebProduct(
                title        = title,
                price        = price,
                currency     = cur,
                rating       = rating,
                review_count = rc,
                source       = "Amazon India" if "amazon.in" in url else "Amazon US",
                url          = full_url,
                image        = image,
                found_via    = "amazon_scraper",
            ))

        return products

    def search_in(self, query: str, limit: int = 5) -> List[WebProduct]:
        """Amazon India (INR prices)."""
        time.sleep(random.uniform(1.0, 2.0))  # polite delay
        return self._scrape(self._search_url(query, "in"), limit)

    def search_us(self, query: str, limit: int = 5) -> List[WebProduct]:
        """Amazon US (USD prices)."""
        time.sleep(random.uniform(1.0, 2.0))
        return self._scrape(self._search_url(query, "com"), limit)


# ─── Tier 4b: Flipkart Scraper ────────────────────────────────────────────────

class FlipkartScraper:
    """
    Scrapes Flipkart search results.
    Flipkart is more scraper-friendly than Amazon.
    """

    BASE = "https://www.flipkart.com/search"

    def search(self, query: str, limit: int = 5) -> List[WebProduct]:
        if not _BS4:
            return []
        try:
            time.sleep(random.uniform(0.8, 1.5))
            sess = _new_session()
            r = sess.get(
                self.BASE,
                params={"q": query},
                headers=_headers({"Referer": "https://www.flipkart.com/"}),
                timeout=14,
            )
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as exc:
            log.warning("Flipkart scrape error: %s", exc)
            return []

        products: List[WebProduct] = []

        # Flipkart uses hashed CSS classes that change; use attribute selectors
        # and look for common patterns instead
        for div in soup.find_all("div", {"data-id": True})[:limit]:
            # Title: usually in an <a> tag with class containing text
            title_el = (
                div.find("a", class_=re.compile(r"IRpwTa|s1Q9rs|CnIBFM|_4rR01T"))
                or div.find("div", class_=re.compile(r"_4rR01T|s1Q9rs"))
            )
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            # Price
            price_el = div.find("div", class_=re.compile(r"_30jeq3|Nx9bqj|_30jeq3"))
            price_text = price_el.get_text(strip=True) if price_el else ""
            price, cur = _parse_price(price_text or div.get_text(" "))

            # Rating
            rating_el = div.find("div", class_=re.compile(r"_3LWZlK|XQDdHH|_I9guX"))
            rating = None
            if rating_el:
                try:
                    rating = float(rating_el.get_text(strip=True))
                    if not (0 <= rating <= 5):
                        rating = None
                except ValueError:
                    pass

            # Link
            link_el = div.find("a", href=True)
            href = link_el["href"] if link_el else ""
            full_url = f"https://www.flipkart.com{href}" if href.startswith("/") else href

            products.append(WebProduct(
                title     = title,
                price     = price,
                currency  = cur or "INR",
                rating    = rating,
                source    = "Flipkart",
                url       = full_url,
                found_via = "flipkart_scraper",
            ))

        return products


# ─── Tier 4c: BestBuy Scraper ─────────────────────────────────────────────────

class BestBuyScraper:
    """Scrapes BestBuy.com product listings."""

    BASE = "https://www.bestbuy.com/site/searchpage.jsp"

    def search(self, query: str, limit: int = 5) -> List[WebProduct]:
        if not _BS4:
            return []
        try:
            time.sleep(random.uniform(1.0, 2.0))
            sess = _new_session()
            r = sess.get(
                self.BASE,
                params={"st": query},
                headers=_headers({"Referer": "https://www.bestbuy.com/"}),
                timeout=12,
            )
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as exc:
            log.warning("BestBuy scrape error: %s", exc)
            return []

        products: List[WebProduct] = []
        for item in soup.select(".sku-item")[:limit]:
            title_el = item.select_one(".sku-title a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            price_el = item.select_one(".priceView-customer-price span")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price, cur = _parse_price(price_text)

            rating_el = item.select_one(".ratings-reviews .c-review-average")
            rating = None
            if rating_el:
                try:
                    rating = float(rating_el.get_text(strip=True))
                except ValueError:
                    pass

            review_el = item.select_one(".c-total-reviews")
            rc = _parse_review_count(review_el.get_text()) if review_el else 0

            href = title_el.get("href", "")
            full_url = f"https://www.bestbuy.com{href}" if href.startswith("/") else href

            products.append(WebProduct(
                title        = title,
                price        = price,
                currency     = "USD",
                rating       = rating,
                review_count = rc,
                source       = "Best Buy",
                url          = full_url,
                found_via    = "bestbuy_scraper",
            ))
        return products


# ─── Tier 4d: Croma Scraper ───────────────────────────────────────────────────

class CromaScraper:
    """Scrapes Croma.com (India) product listings."""

    BASE = "https://www.croma.com/searchB"

    def search(self, query: str, limit: int = 5) -> List[WebProduct]:
        if not _BS4:
            return []
        try:
            time.sleep(random.uniform(0.8, 1.5))
            sess = _new_session()
            r = sess.get(
                self.BASE,
                params={"q": query, "langstore": "en"},
                headers=_headers({"Referer": "https://www.croma.com/"}),
                timeout=12,
            )
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as exc:
            log.warning("Croma scrape error: %s", exc)
            return []

        products: List[WebProduct] = []
        for item in soup.select(".product-item, li.product-item")[:limit]:
            title_el = item.select_one(".product-title, h3")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            price_el = item.select_one(".amount, .price")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price, _ = _parse_price(price_text)

            link_el = item.select_one("a[href]")
            href = link_el["href"] if link_el else ""
            full_url = f"https://www.croma.com{href}" if href.startswith("/") else href

            products.append(WebProduct(
                title     = title,
                price     = price,
                currency  = "INR",
                source    = "Croma",
                url       = full_url,
                found_via = "croma_scraper",
            ))
        return products


# ─── Main orchestrator ────────────────────────────────────────────────────────

class WebSearchEngine:
    """
    Orchestrates all search tiers, merges and deduplicates results.

    Usage:
        engine = WebSearchEngine()
        products = engine.search("gaming laptop under ₹90000", limit=8)
        for p in products:
            print(p.title, p.price, p.currency, p.source)

    The engine auto-detects which tiers are available based on env vars.
    """

    def __init__(self, enable_scrapers: bool = True) -> None:
        self._qgen     = QueryGenerator()
        self._serpapi  = SerpAPISearcher()
        self._google   = GoogleCSESearcher()
        self._ddg      = DuckDuckGoSearcher()
        self._amazon   = AmazonScraper()      if enable_scrapers else None
        self._flipkart = FlipkartScraper()    if enable_scrapers else None
        self._bestbuy  = BestBuyScraper()     if enable_scrapers else None
        self._croma    = CromaScraper()       if enable_scrapers else None

    def available_tiers(self) -> List[str]:
        tiers = []
        if self._serpapi.is_available():  tiers.append("SerpAPI")
        if self._google.is_available():   tiers.append("Google CSE")
        if self._ddg.is_available():      tiers.append("DuckDuckGo")
        if self._amazon and _BS4:         tiers.append("Amazon Scraper")
        if self._flipkart and _BS4:       tiers.append("Flipkart Scraper")
        if self._bestbuy and _BS4:        tiers.append("BestBuy Scraper")
        if self._croma and _BS4:          tiers.append("Croma Scraper")
        return tiers

    def search(
        self,
        query: str,
        limit:          int = 10,
        category:       str = "general",
        budget:         Optional[float] = None,
        currency:       str = "USD",
        use_scrapers:   bool = True,
    ) -> List[WebProduct]:
        """
        Run all available search tiers for the query.
        Returns up to `limit` deduplicated WebProduct objects.
        """
        results: List[WebProduct] = []

        # ── Generate search queries ──────────────────────────────────────
        queries = self._qgen.generate(query, category=category, budget=budget,
                                      currency=currency, limit=3)
        primary_query = queries[0]

        # ── Tier 1: SerpAPI ──────────────────────────────────────────────
        if self._serpapi.is_available() and len(results) < limit:
            try:
                r = self._serpapi.search(primary_query, limit)
                results.extend(r)
                log.info("SerpAPI returned %d results", len(r))
            except Exception as exc:
                log.warning("SerpAPI failed: %s", exc)

        # ── Tier 2: Google CSE ───────────────────────────────────────────
        if self._google.is_available() and len(results) < limit:
            try:
                r = self._google.search(primary_query, limit - len(results))
                results.extend(r)
                log.info("Google CSE returned %d results", len(r))
            except Exception as exc:
                log.warning("Google CSE failed: %s", exc)

        # ── Tier 3: DuckDuckGo (always available fallback) ────────────────
        if len(results) < limit // 2:
            try:
                r = self._ddg.search(primary_query, limit - len(results))
                results.extend(r)
                log.info("DuckDuckGo returned %d results", len(r))
            except Exception as exc:
                log.warning("DuckDuckGo failed: %s", exc)

        # ── Tier 4: Direct scrapers ───────────────────────────────────────
        if use_scrapers and _BS4 and len(results) < limit:
            is_india = (currency == "INR" or any(
                s in query.lower() for s in ["flipkart", "india", "₹", "amazon.in", "croma"]
            ))

            scraper_limit = max(3, limit - len(results))

            if is_india:
                # India searches: Flipkart + Amazon IN + Croma
                if self._flipkart:
                    try:
                        r = self._flipkart.search(query, scraper_limit)
                        results.extend(r)
                        log.info("Flipkart returned %d results", len(r))
                    except Exception as exc:
                        log.warning("Flipkart failed: %s", exc)

                if len(results) < limit and self._croma:
                    try:
                        r = self._croma.search(query, scraper_limit)
                        results.extend(r)
                        log.info("Croma returned %d results", len(r))
                    except Exception as exc:
                        log.warning("Croma failed: %s", exc)

                if len(results) < limit and self._amazon:
                    try:
                        r = self._amazon.search_in(query, scraper_limit)
                        results.extend(r)
                        log.info("Amazon IN returned %d results", len(r))
                    except Exception as exc:
                        log.warning("Amazon IN failed: %s", exc)
            else:
                # Global: BestBuy + Amazon US
                if self._bestbuy:
                    try:
                        r = self._bestbuy.search(query, scraper_limit)
                        results.extend(r)
                        log.info("BestBuy returned %d results", len(r))
                    except Exception as exc:
                        log.warning("BestBuy failed: %s", exc)

                if len(results) < limit and self._amazon:
                    try:
                        r = self._amazon.search_us(query, scraper_limit)
                        results.extend(r)
                        log.info("Amazon US returned %d results", len(r))
                    except Exception as exc:
                        log.warning("Amazon US failed: %s", exc)

        return self._deduplicate(results)[:limit]

    def search_multi_query(
        self,
        query: str,
        limit: int = 10,
        category: str = "general",
        budget: Optional[float] = None,
        currency: str = "USD",
    ) -> List[WebProduct]:
        """
        Run multiple generated queries and merge results for higher coverage.
        Use this for the AI Shopping Assistant flow.
        """
        queries = self._qgen.generate(query, category=category, budget=budget,
                                      currency=currency, limit=3)
        all_results: List[WebProduct] = []
        for q in queries:
            r = self.search(q, limit=limit, currency=currency, use_scrapers=False)
            all_results.extend(r)
            if len(all_results) >= limit * 2:
                break
        return self._deduplicate(all_results)[:limit]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _deduplicate(self, products: List[WebProduct]) -> List[WebProduct]:
        """Remove duplicate results by normalised title similarity."""
        seen: set = set()
        out:  List[WebProduct] = []
        for p in products:
            key = re.sub(r"[^\w]", "", p.title.lower())[:40]
            if key and key not in seen:
                seen.add(key)
                out.append(p)
        return out

    def status(self) -> Dict[str, Any]:
        return {
            "tiers_available": self.available_tiers(),
            "serpapi":    self._serpapi.is_available(),
            "google_cse": self._google.is_available(),
            "duckduckgo": _BS4,
            "scrapers":   _BS4,
            "bs4_installed": _BS4,
        }


# ─── Product Page Scraper ────────────────────────────────────────────────────

def scrape_product_url(url: str) -> Dict[str, Any]:
    """
    Fetches a product page URL and extracts real product data:
      name, price, currency, rating, review_count, image, description.

    Strategy (in order of preference):
      1. JSON-LD schema.org Product/Offer  (most reliable)
      2. Site-specific CSS selectors       (Amazon, Flipkart, Croma, BestBuy)
      3. Open Graph meta tags
      4. ASIN/URL-based search fallback    (when Amazon blocks direct scrape)
      5. <title> tag + generic text price
    """
    if not _BS4:
        log.warning("scrape_product_url: beautifulsoup4 not installed")
        return {}

    import json as _json

    # Browser-realistic headers to reduce bot blocking
    browser_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/",
    }

    domain = urlparse(url).netloc.lower()
    soup = None

    try:
        sess = _new_session()
        r = sess.get(url, headers=browser_headers, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
        else:
            log.warning("scrape_product_url: HTTP %s for %s", r.status_code, url)
    except Exception as exc:
        log.warning("scrape_product_url fetch error: %s", exc)

    result: Dict[str, Any] = {}

    # ── Helper: detect if we got a bot-check / captcha page ──────────────────
    def _is_bot_blocked() -> bool:
        if not soup:
            return True
        body_text = soup.get_text(" ", strip=True).lower()[:500]
        indicators = ["robot check", "captcha", "enter the characters", "sorry, we just need",
                      "automated access", "service unavailable", "access denied"]
        return any(ind in body_text for ind in indicators)

    if soup and not _is_bot_blocked():
        # ── 1. JSON-LD schema.org ─────────────────────────────────────────────
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                raw = script.string or ""
                data = _json.loads(raw)
                if isinstance(data, list):
                    data = next((d for d in data if isinstance(d, dict) and
                                 d.get("@type") in ("Product", "ItemPage")), None) or {}
                if not isinstance(data, dict):
                    continue
                dtype = data.get("@type", "")
                if dtype not in ("Product", "ItemPage") and "Product" not in str(dtype):
                    continue

                if not result.get("name"):
                    result["name"] = data.get("name", "")
                if not result.get("description"):
                    result["description"] = str(data.get("description", ""))[:250]
                if not result.get("image"):
                    img = data.get("image", "")
                    if isinstance(img, list):
                        img = img[0] if img else ""
                    result["image"] = img if isinstance(img, str) else (img.get("url", "") if isinstance(img, dict) else "")
                if not result.get("brand"):
                    brand = data.get("brand", {})
                    result["brand"] = brand.get("name", "") if isinstance(brand, dict) else str(brand)

                agg = data.get("aggregateRating", {})
                if isinstance(agg, dict) and not result.get("rating"):
                    try:
                        result["rating"] = float(agg.get("ratingValue", 0) or 0)
                        result["review_count"] = int(str(agg.get("reviewCount", 0) or agg.get("ratingCount", 0)).replace(",", "") or 0)
                    except (ValueError, TypeError):
                        pass

                offers = data.get("offers", data.get("Offers", {}))
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                if isinstance(offers, dict) and not result.get("price"):
                    raw_price = offers.get("price", offers.get("lowPrice", ""))
                    if raw_price:
                        try:
                            result["price"] = float(str(raw_price).replace(",", ""))
                            result["currency"] = offers.get("priceCurrency", "USD")
                        except (ValueError, TypeError):
                            pass
                    avail = str(offers.get("availability", "")).lower()
                    result["in_stock"] = "instock" in avail.replace(" ", "") or not avail
                break
            except Exception:
                continue

        # ── 2. Site-specific selectors ────────────────────────────────────────
        if "amazon" in domain:
            if not result.get("name"):
                t = soup.select_one("#productTitle") or soup.select_one("#title span")
                if t:
                    result["name"] = t.get_text(strip=True)
            if not result.get("price"):
                for sel in [
                    ".priceToPay .a-price-whole",
                    "#corePriceDisplay_desktop_feature_div .a-price-whole",
                    ".a-price.aok-align-center .a-price-whole",
                    "#priceblock_ourprice",
                    ".a-color-price",
                    "#price_inside_buybox",
                ]:
                    pe = soup.select_one(sel)
                    if pe:
                        price_str = pe.get_text(strip=True).replace(",", "").rstrip(".")
                        frac = soup.select_one(".a-price-fraction")
                        if frac:
                            price_str += "." + frac.get_text(strip=True)
                        p, c = _parse_price(("₹" if "amazon.in" in domain else "$") + price_str)
                        if p:
                            result["price"] = p
                            result["currency"] = "INR" if "amazon.in" in domain else "USD"
                            break
            if not result.get("rating"):
                re_el = soup.select_one("#acrPopover")
                if re_el:
                    rv = _parse_rating(re_el.get("title", "") or re_el.get_text())
                    if rv:
                        result["rating"] = rv
                rc_el = soup.select_one("#acrCustomerReviewText")
                if rc_el:
                    result["review_count"] = _parse_review_count(rc_el.get_text())
            if not result.get("image"):
                img_el = soup.select_one("#landingImage") or soup.select_one("#imgBlkFront")
                if img_el:
                    result["image"] = img_el.get("src") or img_el.get("data-old-hires") or ""

        elif "flipkart" in domain:
            if not result.get("name"):
                t = (soup.select_one(".B_NuCI") or soup.select_one(".yhB1nd") or
                     soup.select_one("h1.G6XhRU") or soup.select_one("h1"))
                if t:
                    result["name"] = t.get_text(strip=True)
            if not result.get("price"):
                p_el = (soup.select_one("._30jeq3._16Jk6d") or soup.select_one("._30jeq3") or
                        soup.select_one(".Nx9bqj"))
                if p_el:
                    p, _ = _parse_price(p_el.get_text(strip=True))
                    if p:
                        result["price"] = p
                        result["currency"] = "INR"
            if not result.get("rating"):
                r_el = soup.select_one("._3LWZlK") or soup.select_one(".XQDdHH")
                if r_el:
                    try:
                        result["rating"] = float(r_el.get_text(strip=True))
                    except (ValueError, TypeError):
                        pass

        elif "croma" in domain:
            if not result.get("name"):
                t = soup.select_one("h1.pdp-title") or soup.select_one("h1")
                if t:
                    result["name"] = t.get_text(strip=True)
            if not result.get("price"):
                p_el = soup.select_one(".pdp-price") or soup.select_one(".amount")
                if p_el:
                    p, _ = _parse_price(p_el.get_text(strip=True))
                    if p:
                        result["price"] = p
                        result["currency"] = "INR"

        elif "bestbuy" in domain:
            if not result.get("name"):
                t = soup.select_one(".sku-title h1") or soup.select_one("h1")
                if t:
                    result["name"] = t.get_text(strip=True)
            if not result.get("price"):
                p_el = soup.select_one(".priceView-customer-price span")
                if p_el:
                    p, _ = _parse_price(p_el.get_text(strip=True))
                    if p:
                        result["price"] = p
                        result["currency"] = "USD"

        # ── 3. Open Graph meta tags ───────────────────────────────────────────
        def _meta(prop: str) -> str:
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            return (tag.get("content", "") if tag else "").strip()

        if not result.get("name"):
            result["name"] = _meta("og:title") or _meta("twitter:title")
        if not result.get("description"):
            result["description"] = (_meta("og:description") or _meta("twitter:description"))[:250]
        if not result.get("image"):
            result["image"] = _meta("og:image") or _meta("twitter:image")
        if not result.get("price"):
            for prop in ("product:price:amount", "og:price:amount", "twitter:data1"):
                pv = _meta(prop)
                if pv:
                    try:
                        result["price"] = float(pv.replace(",", ""))
                        result["currency"] = _meta("product:price:currency") or _meta("og:price:currency") or "USD"
                        break
                    except (ValueError, TypeError):
                        pass

        # ── 4. Title tag fallback ─────────────────────────────────────────────
        if not result.get("name"):
            title_tag = soup.find("title")
            if title_tag:
                raw_title = title_tag.get_text(strip=True)
                for sep in [" | ", " - ", " : ", " — ", " – "]:
                    if sep in raw_title:
                        raw_title = raw_title.split(sep)[0].strip()
                        break
                candidate = raw_title[:120]
                # Reject generic page titles
                if candidate.lower() not in ("amazon.in", "flipkart.com", "amazon.com", "bestbuy.com"):
                    result["name"] = candidate

        if not result.get("price"):
            visible = " ".join(t.get_text(" ") for t in soup.select("body"))[:3000]
            p, c = _parse_price(visible)
            if p:
                result["price"] = p
                result["currency"] = c

    # ── 5. ASIN/URL search fallback (handles Amazon bot-block) ────────────────
    if not result.get("name") or not result.get("price"):
        # Extract ASIN from Amazon URL
        asin_m = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url.upper())
        search_query = None
        if asin_m and "amazon" in domain:
            search_query = asin_m.group(1)  # Search by ASIN
        elif not result.get("name"):
            # Extract words from URL path as search query
            path = re.sub(r'https?://[^/]+', '', url).split('?')[0]
            path = re.sub(r'\b(dp|product|p|item|itm|gp|s|ref|html?|php)\b', ' ', path, flags=re.I)
            path = re.sub(r'\b[A-Z0-9]{10}\b', ' ', path)
            path = re.sub(r'\b\d{5,}\b', ' ', path)
            search_query = ' '.join(re.sub(r'[/_\-+%]', ' ', path).split())[:80] or None

        if search_query:
            try:
                # Prefer SerpAPI — returns structured price+title from Google Shopping
                _serp = SerpAPISearcher()
                if _serp.is_available():
                    serp_results = _serp.search(search_query + " buy", limit=5)
                    for wp in serp_results:
                        if not result.get("name") and wp.title and len(wp.title) > 8:
                            result["name"] = wp.title
                        if not result.get("price") and wp.price and wp.price > 0:
                            result["price"] = wp.price
                            result["currency"] = wp.currency or result.get("currency", "USD")
                        if result.get("name") and result.get("price"):
                            break

                # DDG fallback if SerpAPI unavailable or returned no price
                if (not result.get("name") or not result.get("price")) and _BS4:
                    ddg = DuckDuckGoSearcher()
                    ddg_results = ddg.search(search_query + " buy online price", limit=5)
                    for wp in ddg_results:
                        if not result.get("name") and wp.title and len(wp.title) > 8:
                            result["name"] = wp.title
                        if not result.get("price") and wp.price and wp.price > 50:
                            trusted = any(d in wp.url for d in ("amazon", "flipkart", "bestbuy", "croma", "ebay"))
                            if trusted:
                                result["price"] = wp.price
                                result["currency"] = wp.currency
                        if result.get("name") and result.get("price"):
                            break
                # If we got a name but no price, find_alternatives() will discover real prices
            except Exception as exc:
                log.warning("ASIN/URL search fallback failed: %s", exc)

    # Clean up
    result = {k: v for k, v in result.items() if v not in (None, "", [], {}, 0.0)}
    log.info("scrape_product_url extracted: name=%r price=%s cur=%s",
             result.get("name", "?"), result.get("price", "?"), result.get("currency", "?"))
    return result
    if not _BS4:
        log.warning("scrape_product_url: beautifulsoup4 not installed")
        return {}

    import json as _json

    try:
        sess = _new_session()
        r = sess.get(
            url,
            headers=_headers({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.google.com/",
            }),
            timeout=15,
            allow_redirects=True,
        )
        if r.status_code != 200:
            log.warning("scrape_product_url: HTTP %s for %s", r.status_code, url)
            return {}
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as exc:
        log.warning("scrape_product_url fetch error: %s", exc)
        return {}

    result: Dict[str, Any] = {}
    domain = urlparse(url).netloc.lower()

    # ── 1. JSON-LD schema.org (most reliable) ────────────────────────────────
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            raw = script.string or ""
            data = _json.loads(raw)
            # Handle both single dict and list
            if isinstance(data, list):
                data = next((d for d in data if isinstance(d, dict) and
                             d.get("@type") in ("Product", "ItemPage")), None) or {}
            if not isinstance(data, dict):
                continue
            dtype = data.get("@type", "")
            if dtype not in ("Product", "ItemPage") and "Product" not in str(dtype):
                continue

            if not result.get("name"):
                result["name"] = data.get("name", "")
            if not result.get("description"):
                result["description"] = str(data.get("description", ""))[:250]
            if not result.get("image"):
                img = data.get("image", "")
                if isinstance(img, list):
                    img = img[0] if img else ""
                result["image"] = img if isinstance(img, str) else (img.get("url","") if isinstance(img, dict) else "")
            if not result.get("brand"):
                brand = data.get("brand", {})
                if isinstance(brand, dict):
                    result["brand"] = brand.get("name", "")
                elif isinstance(brand, str):
                    result["brand"] = brand

            # Rating from aggregateRating
            agg = data.get("aggregateRating", {})
            if isinstance(agg, dict) and not result.get("rating"):
                try:
                    result["rating"] = float(agg.get("ratingValue", 0) or 0)
                    result["review_count"] = int(str(agg.get("reviewCount", 0) or agg.get("ratingCount", 0)).replace(",", "") or 0)
                except (ValueError, TypeError):
                    pass

            # Price from offers
            offers = data.get("offers", data.get("Offers", {}))
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if isinstance(offers, dict) and not result.get("price"):
                raw_price = offers.get("price", offers.get("lowPrice", ""))
                if raw_price:
                    try:
                        result["price"] = float(str(raw_price).replace(",", ""))
                        result["currency"] = offers.get("priceCurrency", "USD")
                    except (ValueError, TypeError):
                        pass
                avail = str(offers.get("availability", "")).lower()
                result["in_stock"] = "instock" in avail or "instock" in avail.replace(" ", "") or not avail
            break
        except Exception:
            continue

    # ── 2. Site-specific selectors ────────────────────────────────────────────

    if "amazon" in domain:
        # Title
        if not result.get("name"):
            t = soup.select_one("#productTitle") or soup.select_one("#title span")
            if t:
                result["name"] = t.get_text(strip=True)
        # Price
        if not result.get("price"):
            # Try multiple Amazon price locations
            for sel in [
                ".priceToPay .a-price-whole",
                "#corePriceDisplay_desktop_feature_div .a-price-whole",
                ".a-price.aok-align-center .a-price-whole",
                "#priceblock_ourprice",
                ".a-color-price",
                "#price_inside_buybox",
            ]:
                pe = soup.select_one(sel)
                if pe:
                    price_str = pe.get_text(strip=True).replace(",", "").rstrip(".")
                    frac = soup.select_one(".a-price-fraction")
                    if frac:
                        price_str += "." + frac.get_text(strip=True)
                    p, c = _parse_price("₹" + price_str if "amazon.in" in domain else "$" + price_str)
                    if p:
                        result["price"] = p
                        result["currency"] = "INR" if "amazon.in" in domain else "USD"
                        break
        # Rating
        if not result.get("rating"):
            re_el = soup.select_one("#acrPopover")
            if re_el:
                r_txt = re_el.get("title", "") or re_el.get_text()
                rv = _parse_rating(r_txt)
                if rv:
                    result["rating"] = rv
            rc_el = soup.select_one("#acrCustomerReviewText")
            if rc_el:
                result["review_count"] = _parse_review_count(rc_el.get_text())
        # Image
        if not result.get("image"):
            img_el = soup.select_one("#landingImage") or soup.select_one("#imgBlkFront")
            if img_el:
                result["image"] = (img_el.get("src") or img_el.get("data-old-hires") or
                                   img_el.get("data-a-dynamic-image", "").split('"')[1:2] or [""])[0]

    elif "flipkart" in domain:
        if not result.get("name"):
            t = (soup.select_one(".B_NuCI") or soup.select_one(".yhB1nd") or
                 soup.select_one("h1.G6XhRU") or soup.select_one("h1"))
            if t:
                result["name"] = t.get_text(strip=True)
        if not result.get("price"):
            p_el = (soup.select_one("._30jeq3._16Jk6d") or soup.select_one("._30jeq3") or
                    soup.select_one(".Nx9bqj"))
            if p_el:
                p, _ = _parse_price(p_el.get_text(strip=True))
                if p:
                    result["price"] = p
                    result["currency"] = "INR"
        if not result.get("rating"):
            r_el = soup.select_one("._3LWZlK") or soup.select_one(".XQDdHH")
            if r_el:
                try:
                    result["rating"] = float(r_el.get_text(strip=True))
                except (ValueError, TypeError):
                    pass

    elif "croma" in domain:
        if not result.get("name"):
            t = soup.select_one("h1.pdp-title") or soup.select_one("h1")
            if t:
                result["name"] = t.get_text(strip=True)
        if not result.get("price"):
            p_el = soup.select_one(".pdp-price") or soup.select_one(".amount")
            if p_el:
                p, _ = _parse_price(p_el.get_text(strip=True))
                if p:
                    result["price"] = p
                    result["currency"] = "INR"

    elif "bestbuy" in domain:
        if not result.get("name"):
            t = soup.select_one(".sku-title h1") or soup.select_one("h1")
            if t:
                result["name"] = t.get_text(strip=True)
        if not result.get("price"):
            p_el = soup.select_one(".priceView-customer-price span")
            if p_el:
                p, _ = _parse_price(p_el.get_text(strip=True))
                if p:
                    result["price"] = p
                    result["currency"] = "USD"

    # ── 3. Open Graph meta tags ───────────────────────────────────────────────
    def _meta(prop: str) -> str:
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        return (tag.get("content", "") if tag else "").strip()

    if not result.get("name"):
        result["name"] = _meta("og:title") or _meta("twitter:title")
    if not result.get("description"):
        result["description"] = (_meta("og:description") or _meta("twitter:description"))[:250]
    if not result.get("image"):
        result["image"] = _meta("og:image") or _meta("twitter:image")
    if not result.get("price"):
        for prop in ("product:price:amount", "og:price:amount", "twitter:data1"):
            pv = _meta(prop)
            if pv:
                try:
                    result["price"] = float(pv.replace(",", ""))
                    result["currency"] = _meta("product:price:currency") or _meta("og:price:currency") or "USD"
                    break
                except (ValueError, TypeError):
                    pass

    # ── 4. Last-resort fallbacks ──────────────────────────────────────────────
    if not result.get("name"):
        title_tag = soup.find("title")
        if title_tag:
            raw_title = title_tag.get_text(strip=True)
            # Strip store name from end (e.g. "iPhone 15 | Amazon.in")
            for sep in [" | ", " - ", " : ", " — ", " – "]:
                if sep in raw_title:
                    raw_title = raw_title.split(sep)[0].strip()
                    break
            result["name"] = raw_title[:120]

    if not result.get("price"):
        # Scan first 3000 chars of visible text for any price pattern
        visible = " ".join(t.get_text(" ") for t in soup.select("body"))[:3000]
        p, c = _parse_price(visible)
        if p:
            result["price"] = p
            result["currency"] = c

    # Clean up empty strings
    result = {k: v for k, v in result.items() if v not in (None, "", [], {})}
    log.info("scrape_product_url extracted: name=%r price=%s cur=%s",
             result.get("name","?"), result.get("price","?"), result.get("currency","?"))
    return result


# ─── Singleton ────────────────────────────────────────────────────────────────

# Shared instance used by pipeline.py
web_search_engine = WebSearchEngine()
