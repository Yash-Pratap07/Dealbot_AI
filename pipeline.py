"""
DealBot AI Full Pipeline
========================
Product Discovery Engine
  → Price Comparison Engine
    → Seller Trust & Review Analyzer
      → AI Ranking Engine
        → Human Selection
          → Negotiation Engine  (existing orchestrator.py)
            → Contract Generator
              → Blockchain Storage
                → Payment System (payment.py)
"""
import re
import random
import math
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# Web search integration — optional, gracefully disabled if not installed
try:
    from web_search import web_search_engine as _WEB_ENGINE, WebProduct as _WebProduct, scrape_product_url as _scrape_product_url
    _WEB_ENABLED = True
except Exception:
    _WEB_ENGINE             = None   # type: ignore
    _WEB_ENABLED            = False
    def _scrape_product_url(url: str) -> dict: return {}  # type: ignore


# ─── Currency Conversion ──────────────────────────────────────────────────────

_FX_TO_INR: Dict[str, float] = {
    "USD": 83.5,
    "EUR": 91.0,
    "GBP": 106.0,
    "INR": 1.0,
}

def _convert_to_inr(price: float, from_currency: str) -> float:
    """Convert a price from any supported currency to INR."""
    rate = _FX_TO_INR.get(from_currency.upper(), 83.5)  # default assumes USD
    return round(price * rate, 2)

def _convert_currency(price: float, from_cur: str, to_cur: str) -> float:
    """Convert between any two supported currencies via INR."""
    if from_cur == to_cur:
        return price
    inr = price * _FX_TO_INR.get(from_cur.upper(), 83.5)
    to_rate = _FX_TO_INR.get(to_cur.upper(), 1.0)
    return round(inr / to_rate, 2)


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Product:
    id: str
    name: str
    category: str
    description: str
    emoji: str
    tags: List[str]
    image: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "emoji": self.emoji,
            "tags": self.tags,
            "image": self.image,
        }


@dataclass
class SellerListing:
    listing_id: str
    product: Product
    seller_id: str
    seller_name: str
    price: float
    currency: str
    condition: str
    location: str
    stock: int
    rating: float
    review_count: int
    reviews: List[str]
    response_time: str
    verified: bool
    trust_score: float = 0.0
    rank_score: float = 0.0
    price_rank: int = 0
    trust_rank: int = 0
    price_percentile: float = 0.0   # 0=cheapest, 100=most expensive
    url: str = ""
    image: str = ""

    def to_dict(self) -> dict:
        return {
            "listing_id": self.listing_id,
            "product": self.product.to_dict(),
            "seller_id": self.seller_id,
            "seller_name": self.seller_name,
            "price": self.price,
            "currency": self.currency,
            "condition": self.condition,
            "location": self.location,
            "stock": self.stock,
            "rating": self.rating,
            "review_count": self.review_count,
            "reviews": self.reviews[:3],   # top 3 reviews
            "response_time": self.response_time,
            "verified": self.verified,
            "trust_score": round(self.trust_score, 2),
            "rank_score": round(self.rank_score, 2),
            "price_rank": self.price_rank,
            "trust_rank": self.trust_rank,
            "price_percentile": round(self.price_percentile, 1),
            "url": self.url,
            "image": self.image or self.product.image,
        }


# ─── Mock Catalog ─────────────────────────────────────────────────────────────

_CATALOG: List[Product] = [
    Product("p001", "iPhone 16 Pro 256GB",       "Electronics",  "Apple A18 Pro chip, titanium design, 48MP camera system",         "📱", ["iphone","apple","smartphone","ios","mobile"]),
    Product("p002", "Samsung Galaxy S25 Ultra",  "Electronics",  "Samsung flagship with 200MP camera system and built-in S Pen",    "📱", ["samsung","android","smartphone","galaxy","mobile"]),
    Product("p003", "Sony WH-1000XM6",           "Audio",        "Industry-leading noise cancelling wireless headphones",            "🎧", ["headphones","sony","audio","wireless","noise-cancelling"]),
    Product("p004", "MacBook Pro M4 16\"",        "Computers",    "Apple M4 Pro chip, Liquid Retina XDR display, 22h battery",       "💻", ["macbook","apple","laptop","mac","pro"]),
    Product("p005", "Dell XPS 15 9530",          "Computers",    "Premium Windows laptop with OLED display and RTX 4060",           "💻", ["dell","laptop","windows","xps","oled"]),
    Product("p006", "Nike Air Max 2025",         "Footwear",     "Iconic running shoes with next-gen Air Max cushioning unit",      "👟", ["nike","shoes","running","footwear","airmax"]),
    Product("p007", "PlayStation 6",             "Gaming",       "Sony next-gen console with 8K gaming and immersive haptics",      "🎮", ["ps6","sony","console","gaming","playstation"]),
    Product("p008", "LG OLED C5 65\"",           "TV & Display", "Gallery OLED evo panel, Dolby Vision IQ, 4x HDMI 2.1",           "📺", ["lg","tv","oled","4k","television"]),
    Product("p009", "Dyson V16 Detect",          "Home",         "Cordless vacuum with HEPA filtration and laser dust detection",   "🌀", ["dyson","vacuum","cordless","home","cleaning"]),
    Product("p010", "Canon EOS R6 Mark III",     "Camera",       "Full-frame mirrorless, 40fps burst, in-body stabilisation",      "📷", ["canon","camera","mirrorless","photography","fullframe"]),
    Product("p011", "iPad Pro M4 13\"",          "Tablets",      "M4 chip, Ultra-Retina XDR OLED, Apple Pencil Pro support",       "📲", ["ipad","apple","tablet","pro","ios"]),
    Product("p012", "Rolex Submariner",          "Watches",      "Swiss luxury dive watch, 300m waterproof, Oystersteel bracelet", "⌚", ["rolex","watch","luxury","swiss","submariner"]),
    Product("p013", "Herman Miller Aeron C",     "Furniture",    "PostureFit SL lumbar support, fully adjustable ergonomic chair", "🪑", ["herman miller","chair","ergonomic","office","furniture"]),
    Product("p014", "AirPods Pro 3",             "Audio",        "Active noise cancellation, spatial audio, H3 chip",              "🎵", ["airpods","apple","earbuds","wireless","audio"]),
    Product("p015", "DJI Mavic 4 Pro",           "Drones",       "Hasselblad camera, 46min flight time, omnidirectional sensing",  "🚁", ["dji","drone","camera","photography","mavic"]),
    Product("p016", "Tesla Model Y Wheel Set",   "Automotive",   "21-inch forged alloy wheels with performance tyres",             "⚙️", ["tesla","wheels","automotive","model-y","ev"]),
    Product("p017", "Nvidia RTX 5090",           "Components",   "Flagship GPU with 128GB GDDR7 and Blackwell architecture",       "🖥️", ["nvidia","gpu","rtx","graphics","pc"]),
    Product("p018", "Bose QuietComfort Ultra",   "Audio",        "World-class noise cancellation with immersive spatial audio",    "🎧", ["bose","headphones","noise-cancelling","wireless","audio"]),
]

_SELLERS = [
    {"id": "s001", "name": "TechMart Pro",      "markup": 1.05, "rating": 4.8, "reviews": 2341, "verified": True,  "response": "2h",  "location": "New York"},
    {"id": "s002", "name": "DealZone",           "markup": 0.93, "rating": 4.2, "reviews": 867,  "verified": True,  "response": "6h",  "location": "Chicago"},
    {"id": "s003", "name": "QuickShip Store",    "markup": 1.08, "rating": 3.9, "reviews": 421,  "verified": False, "response": "12h", "location": "Dallas"},
    {"id": "s004", "name": "PremiumGoods",       "markup": 1.15, "rating": 4.9, "reviews": 5120, "verified": True,  "response": "1h",  "location": "Los Angeles"},
    {"id": "s005", "name": "BudgetBuy",          "markup": 0.87, "rating": 3.5, "reviews": 203,  "verified": False, "response": "24h", "location": "Houston"},
    {"id": "s006", "name": "GlobalTech Hub",     "markup": 1.02, "rating": 4.6, "reviews": 1890, "verified": True,  "response": "3h",  "location": "Seattle"},
    {"id": "s007", "name": "ValueShop",          "markup": 0.91, "rating": 4.0, "reviews": 654,  "verified": True,  "response": "8h",  "location": "Miami"},
]

_BASE_PRICES: Dict[str, float] = {
    "p001": 99499.0,  "p002": 107799.0, "p003": 28999.0,  "p004": 207499.0,
    "p005": 157599.0, "p006": 14999.0,  "p007": 49699.0,  "p008": 182499.0,
    "p009": 70499.0,  "p010": 248999.0, "p011": 107799.0, "p012": 788499.0,
    "p013": 119999.0, "p014": 20699.0,  "p015": 273999.0, "p016": 74599.0,
    "p017": 207499.0, "p018": 35599.0,
}

_REVIEWS = [
    "Excellent quality, arrived well-packaged!",
    "Best price I found anywhere online.",
    "Seller communicated promptly, very professional.",
    "Exactly as described. Very happy with purchase.",
    "Had a minor issue but seller resolved it within hours.",
    "Outstanding build quality, premium feel.",
    "Fast delivery, product flawless.",
    "Good value for money, would recommend.",
    "Packaging was slightly damaged but product is perfect.",
    "One of my best purchases this year!",
    "Great deal, seller is very trustworthy.",
    "Shipping was quick, item exactly as listed.",
]

_CONDITIONS = ["new", "new", "new", "refurbished", "used"]


# ─── Web → Pipeline Converter ────────────────────────────────────────────────

def _web_products_to_listings(
    web_products: list,
    limit: int,
    target_currency: str = "INR",
) -> tuple:
    """
    Convert WebProduct objects from web_search.py into
    (List[Product], List[SellerListing]) pairs the pipeline can process.
    Prices are converted to target_currency (default INR).
    """
    products: List[Product]       = []
    listings: List[SellerListing] = []
    seen: set                     = set()

    for wp in web_products:                           # wp is a WebProduct
        if not wp.price or wp.price <= 0:
            continue
        title_key = re.sub(r"[^\w]", "", wp.title.lower())[:40]
        if not title_key or title_key in seen:
            continue
        seen.add(title_key)

        # Convert price from source currency to target currency
        source_cur = wp.currency or "USD"
        converted_price = _convert_currency(wp.price, source_cur, target_currency)

        product = Product(
            id          = f"web_{uuid.uuid4().hex[:8]}",
            name        = wp.title[:80],
            category    = wp.category or "Electronics",
            description = wp.snippet[:120] if wp.snippet else f"{wp.category} product",
            emoji       = wp.emoji or "📦",
            tags        = [w for w in re.sub(r"[^\w\s]", "", wp.title.lower()).split() if len(w) > 2][:6],
            image       = wp.image or "",
        )
        listing = SellerListing(
            listing_id   = f"web_{uuid.uuid4().hex[:8]}",
            product      = product,
            seller_id    = f"web_{uuid.uuid4().hex[:6]}",
            seller_name  = wp.source or "Online Store",
            price        = converted_price,
            currency     = target_currency,
            condition    = "new",
            location     = "Online",
            stock        = random.randint(5, 50),
            rating       = wp.rating if wp.rating else round(random.uniform(3.8, 4.8), 1),
            review_count = wp.review_count if wp.review_count else random.randint(50, 2000),
            reviews      = [],
            response_time = "24h",
            verified     = wp.url.startswith("https://"),
            url          = wp.url,
            image        = wp.image or "",
        )
        products.append(product)
        listings.append(listing)
        if len(products) >= limit:
            break

    return products, listings


# ─── Engine 1: Product Discovery ──────────────────────────────────────────────

class ProductDiscoveryEngine:
    """
    Searches the product catalog for items matching the user's query.
    Uses keyword matching across name, category, description, and tags.
    """

    def search(self, query: str, limit: int = 6) -> List[Product]:
        q = query.lower().strip()
        if not q:
            return random.sample(_CATALOG, min(limit, len(_CATALOG)))

        scored: List[tuple[int, Product]] = []
        for product in _CATALOG:
            score = 0
            # Name match is strongest signal
            if q in product.name.lower():
                score += 10
            # Exact tag match
            for tag in product.tags:
                if q in tag or tag in q:
                    score += 5
            # Category match
            if q in product.category.lower():
                score += 3
            # Description match
            if q in product.description.lower():
                score += 2
            # Partial word overlap
            for word in q.split():
                if any(word in t for t in product.tags):
                    score += 1
                if word in product.name.lower():
                    score += 2
            if score > 0:
                scored.append((score, product))

        # Sort by relevance, return top results
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [p for _, p in scored[:limit]]

        # If nothing found, return popular products as fallback
        if not results:
            results = random.sample(_CATALOG[:8], min(limit, 6))

        return results

    def search_web(
        self, query: str, limit: int = 6, currency: str = "INR"
    ) -> Optional[tuple]:
        """
        Try real-time web search via web_search.py.
        Returns (products, listings) tuple, or None if unavailable.
        Searches for best-price alternatives by appending price keywords.
        """
        if not _WEB_ENABLED or _WEB_ENGINE is None:
            return None
        try:
            # Search for cheap/best-price alternatives
            search_query = f"{query} best price buy cheap"
            web_products = _WEB_ENGINE.search(
                search_query, limit=limit * 2,
                currency=currency,
                use_scrapers=True,
            )
            if not web_products:
                return None
            prods, lsts = _web_products_to_listings(web_products, limit, target_currency=currency)
            if not prods:
                return None
            return prods, lsts
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Web search failed: %s", exc)
            return None

    def get_listings_for_products(self, products: List[Product]) -> List[SellerListing]:
        """Generate realistic seller listings for discovered products."""
        listings: List[SellerListing] = []
        for product in products:
            base_price = _BASE_PRICES.get(product.id, 500.0)
            # Each product gets 2-4 seller listings
            num_sellers = random.randint(2, min(4, len(_SELLERS)))
            chosen_sellers = random.sample(_SELLERS, num_sellers)
            for seller in chosen_sellers:
                # Add random price variance ±5%
                variance = random.uniform(-0.05, 0.05)
                price = round(base_price * seller["markup"] * (1 + variance), 2)
                condition = random.choice(_CONDITIONS)
                listing = SellerListing(
                    listing_id=f"lst_{uuid.uuid4().hex[:8]}",
                    product=product,
                    seller_id=seller["id"],
                    seller_name=seller["name"],
                    price=price,
                    currency="INR",
                    condition=condition,
                    location=seller["location"],
                    stock=random.randint(1, 50),
                    rating=seller["rating"] + random.uniform(-0.2, 0.2),
                    review_count=seller["reviews"] + random.randint(-50, 100),
                    reviews=random.sample(_REVIEWS, min(5, len(_REVIEWS))),
                    response_time=seller["response"],
                    verified=seller["verified"],
                )
                listings.append(listing)
        return listings


# ─── Engine 2: Price Comparison ───────────────────────────────────────────────

class PriceComparisonEngine:
    """
    Compares prices across all seller listings for each product.
    Computes min, max, avg prices and assigns a price percentile to each listing.
    """

    def compare(self, listings: List[SellerListing]) -> Dict[str, Any]:
        # Group by product id
        by_product: Dict[str, List[SellerListing]] = {}
        for lst in listings:
            pid = lst.product.id
            by_product.setdefault(pid, []).append(lst)

        summary: Dict[str, Dict] = {}
        for pid, prod_listings in by_product.items():
            prices = [l.price for l in prod_listings]
            min_p  = min(prices)
            max_p  = max(prices)
            avg_p  = sum(prices) / len(prices)
            spread = ((max_p - min_p) / avg_p * 100) if avg_p > 0 else 0

            summary[pid] = {
                "product_id": pid,
                "min_price":  round(min_p, 2),
                "max_price":  round(max_p, 2),
                "avg_price":  round(avg_p, 2),
                "spread_pct": round(spread, 1),
                "listing_count": len(prod_listings),
                "savings_vs_max": round(max_p - min_p, 2),
            }

            # Assign price percentile to each listing (0 = cheapest, 100 = most expensive)
            price_range = max_p - min_p
            for lst in prod_listings:
                if price_range > 0:
                    lst.price_percentile = round((lst.price - min_p) / price_range * 100, 1)
                else:
                    lst.price_percentile = 50.0

        # Sort listings by price within each product and set price_rank
        for pid, prod_listings in by_product.items():
            sorted_listings = sorted(prod_listings, key=lambda x: x.price)
            for rank, lst in enumerate(sorted_listings, start=1):
                lst.price_rank = rank

        return summary


# ─── Engine 3: Seller Trust & Review Analyzer ─────────────────────────────────

class SellerTrustAnalyzer:
    """
    Computes a trust score (0-100) for each seller listing.
    Factors: star rating, review count, verified status, response time.
    """

    _RESPONSE_SCORE = {"1h": 10, "2h": 9, "3h": 8, "6h": 6, "8h": 5, "12h": 3, "24h": 1}

    def analyze(self, listings: List[SellerListing]) -> None:
        """Mutates each listing in-place with a computed trust_score."""
        for lst in listings:
            # Rating score: normalise 0-5 → 0-40 points
            rating_score = (lst.rating / 5.0) * 40

            # Review volume score: log-scale up to 20 points
            # 1000+ reviews → 20 points, 100 → ~13, 10 → ~7
            review_score = min(20, math.log10(max(lst.review_count, 1)) / math.log10(5000) * 20)

            # Verified badge: 20 points
            verified_score = 20 if lst.verified else 0

            # Response time: up to 10 points
            response_score = self._RESPONSE_SCORE.get(lst.response_time, 3)

            # Condition bonus for 'new': up to 10 points
            condition_score = 10 if lst.condition == "new" else (5 if lst.condition == "refurbished" else 0)

            lst.trust_score = min(100, rating_score + review_score + verified_score + response_score + condition_score)

        # Assign trust_rank per product
        by_product: Dict[str, List[SellerListing]] = {}
        for lst in listings:
            by_product.setdefault(lst.product.id, []).append(lst)
        for prod_listings in by_product.values():
            sorted_by_trust = sorted(prod_listings, key=lambda x: x.trust_score, reverse=True)
            for rank, lst in enumerate(sorted_by_trust, start=1):
                lst.trust_rank = rank


# ─── Engine 4: AI Ranking Engine ──────────────────────────────────────────────

class AIRankingEngine:
    """
    Multi-factor AI ranking combining price competitiveness and seller trust.
    Produces a final rank_score (0-100) per listing.

    Weight distribution:
      - Trust score:         45%
      - Price competitiveness: 40%  (lower price = higher score)
      - Stock availability:   15%
    """

    TRUST_WEIGHT = 0.45
    PRICE_WEIGHT = 0.40
    STOCK_WEIGHT = 0.15

    def rank(self, listings: List[SellerListing]) -> List[SellerListing]:
        """Returns listings sorted by rank_score (best first), mutates rank_score in-place."""
        if not listings:
            return listings

        by_product: Dict[str, List[SellerListing]] = {}
        for lst in listings:
            by_product.setdefault(lst.product.id, []).append(lst)

        # When every product has only 1 listing (e.g. web search results),
        # compare prices globally so cheaper items rank higher.
        use_global = all(len(v) == 1 for v in by_product.values())

        if use_global:
            all_prices = [l.price for l in listings]
            g_max, g_min = max(all_prices), min(all_prices)
            g_range = g_max - g_min
            g_max_stock = max((l.stock for l in listings), default=1)

            for lst in listings:
                price_score = ((g_max - lst.price) / g_range) * 100 if g_range > 0 else 50
                stock_score = (lst.stock / g_max_stock) * 100 if g_max_stock > 0 else 50
                lst.rank_score = (
                    lst.trust_score * self.TRUST_WEIGHT +
                    price_score     * self.PRICE_WEIGHT +
                    stock_score     * self.STOCK_WEIGHT
                )
        else:
            for prod_listings in by_product.values():
                prices = [l.price for l in prod_listings]
                max_p, min_p = max(prices), min(prices)
                price_range = max_p - min_p
                max_stock = max((l.stock for l in prod_listings), default=1)

                for lst in prod_listings:
                    price_score = ((max_p - lst.price) / price_range) * 100 if price_range > 0 else 50
                    stock_score = (lst.stock / max_stock) * 100 if max_stock > 0 else 50
                    lst.rank_score = (
                        lst.trust_score * self.TRUST_WEIGHT +
                        price_score     * self.PRICE_WEIGHT +
                        stock_score     * self.STOCK_WEIGHT
                    )

        return sorted(listings, key=lambda x: x.rank_score, reverse=True)


# ─── Pipeline Orchestrator ────────────────────────────────────────────────────

def run_pipeline(
    query: str,
    limit: int = 6,
    currency: str = "INR",
) -> Dict[str, Any]:
    """
    Runs the full pre-negotiation pipeline:
      1. Product Discovery  (live web → catalog fallback)
      2. Price Comparison
      3. Trust Analysis
      4. AI Ranking

    Returns a rich dict the API layer can serialise and send to the frontend.
    """
    discovery   = ProductDiscoveryEngine()
    price_cmp   = PriceComparisonEngine()
    trust       = SellerTrustAnalyzer()
    ranker      = AIRankingEngine()

    # Stage 1 – Discovery (prefer live web; fall back to mock catalog)
    web_result = discovery.search_web(query, limit=limit, currency=currency)
    if web_result:
        products, listings = web_result
        data_source = "live_web"
    else:
        products = discovery.search(query, limit=limit)
        listings = discovery.get_listings_for_products(products)
        # Override currency in mock listings
        for lst in listings:
            lst.currency = currency
        data_source = "catalog"

    # Stage 2 – Price comparison
    price_summary = price_cmp.compare(listings)

    # Stage 3 – Trust analysis (mutates listings)
    trust.analyze(listings)

    # Stage 4 – AI Ranking (returns sorted list)
    ranked_listings = ranker.rank(listings)

    # Stage 5 – Second-hand / Refurbished suggestions
    secondhand_listings: List[dict] = []
    if _WEB_ENABLED and _WEB_ENGINE is not None:
        try:
            sh_queries = [
                f"used {query} price",
                f"refurbished {query} buy",
                f"second hand {query}",
            ]
            sh_seen: set = set()
            for sh_q in sh_queries:
                sh_results = _WEB_ENGINE.search(
                    sh_q, limit=4, currency=currency, use_scrapers=True,
                )
                if not sh_results:
                    continue
                for wp in sh_results:
                    if not wp.price or wp.price <= 0:
                        continue
                    key = re.sub(r"[^\w]", "", wp.title.lower())[:40]
                    if key in sh_seen:
                        continue
                    sh_seen.add(key)
                    # Convert price to target currency
                    sh_source_cur = wp.currency or "USD"
                    sh_converted = _convert_currency(wp.price, sh_source_cur, currency)
                    secondhand_listings.append({
                        "title": wp.title[:80],
                        "price": sh_converted,
                        "currency": currency,
                        "source": wp.source or "Online Store",
                        "url": wp.url,
                        "image": wp.image or "",
                        "condition": "used / refurbished",
                        "rating": wp.rating if wp.rating else round(random.uniform(3.5, 4.5), 1),
                        "snippet": wp.snippet[:120] if wp.snippet else "",
                    })
                    if len(secondhand_listings) >= 6:
                        break
                if len(secondhand_listings) >= 6:
                    break
        except Exception:
            pass  # second-hand search is best-effort

    return {
        "query": query,
        "products_found": len(products),
        "listings_found": len(ranked_listings),
        "data_source": data_source,
        "web_search_enabled": _WEB_ENABLED,
        "products": [p.to_dict() for p in products],
        "listings":  [l.to_dict() for l in ranked_listings],
        "secondhand": secondhand_listings,
        "price_summary": price_summary,
        "pipeline_stages": [
            {"id": 1, "name": "Product Discovery",             "status": "done", "count": len(products)},
            {"id": 2, "name": "Price Comparison Engine",       "status": "done", "count": len(ranked_listings)},
            {"id": 3, "name": "Seller Trust & Review Analyzer","status": "done", "count": len(ranked_listings)},
            {"id": 4, "name": "AI Ranking Engine",             "status": "done", "count": len(ranked_listings)},
            {"id": 5, "name": "Second-Hand Product Finder",    "status": "done", "count": len(secondhand_listings)},
        ],
    }


# ─── Shopping Assistant ────────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "gaming_laptop": ["gaming laptop", "gaming  laptop", "gaming nb", "rog", "legion", "nitro", "omen", "alienware", "rtx laptop"],
    "laptop":        ["laptop", "notebook", "macbook", "thinkpad", "xps", "ultrabook", "chromebook", "surface pro"],
    "smartphone":    ["phone", "mobile", "iphone", "samsung galaxy", "oneplus", "poco", "pixel", "android phone", "5g phone"],
    "headphones":    ["headphone", "headset", "earphone", "earbud", "airpod", "buds", "in-ear", "over-ear", "noise cancell"],
    "camera":        ["camera", "dslr", "mirrorless", "canon eos", "nikon", "sony alpha", "photography", "action cam"],
    "tv":            ["tv", "television", "oled tv", "qled", "led tv", "smart tv", "4k tv", "8k tv"],
    "tablet":        ["tablet", "ipad", "android tablet", "surface go"],
    "gpu":           ["graphics card", "gpu", "rtx 40", "rx 7900", "radeon", "geforce"],
    "smartwatch":    ["smartwatch", "smart watch", "apple watch", "galaxy watch", "fitbit"],
    "speaker":       ["speaker", "soundbar", "bluetooth speaker", "jbl", "harman"],
    "drone":         ["drone", "dji", "mavic", "quadcopter", "fpv"],
    "general":       [],
}

_PREFERENCE_QUESTIONS: Dict[str, List[Dict]] = {
    "gaming_laptop": [
        {"id": "gpu",     "label": "GPU",          "emoji": "🎮",
         "options": ["RTX 4050", "RTX 4060", "RTX 4070", "RTX 4080", "Any GPU"]},
        {"id": "ram",     "label": "RAM",           "emoji": "💾",
         "options": ["8GB", "16GB", "32GB", "Any"]},
        {"id": "screen",  "label": "Screen Size",   "emoji": "🖥️",
         "options": ["14\"", "15.6\"", "17.3\"", "Any"]},
        {"id": "brand",   "label": "Brand",         "emoji": "🏷️",
         "options": ["ASUS ROG", "Lenovo Legion", "HP Omen", "Dell Alienware", "Acer Nitro", "Any"]},
        {"id": "storage", "label": "Storage",       "emoji": "💽",
         "options": ["512GB SSD", "1TB SSD", "2TB SSD", "Any"]},
    ],
    "laptop": [
        {"id": "os",    "label": "OS",             "emoji": "💻",
         "options": ["Windows", "macOS", "ChromeOS", "Any"]},
        {"id": "ram",   "label": "RAM",            "emoji": "💾",
         "options": ["8GB", "16GB", "32GB", "Any"]},
        {"id": "usage", "label": "Primary Use",    "emoji": "⚡",
         "options": ["Work / Office", "Programming", "Video Editing", "General Use"]},
        {"id": "brand", "label": "Brand",          "emoji": "🏷️",
         "options": ["Apple", "Dell", "HP", "Lenovo", "ASUS", "Any"]},
    ],
    "smartphone": [
        {"id": "os",      "label": "Platform",     "emoji": "📱",
         "options": ["iOS (iPhone)", "Android", "Any"]},
        {"id": "storage", "label": "Storage",      "emoji": "💾",
         "options": ["128GB", "256GB", "512GB", "1TB", "Any"]},
        {"id": "camera",  "label": "Camera",       "emoji": "📷",
         "options": ["Pro / Triple Camera", "Standard", "Any"]},
        {"id": "brand",   "label": "Brand",        "emoji": "🏷️",
         "options": ["Apple", "Samsung", "Google Pixel", "OnePlus", "Any"]},
    ],
    "headphones": [
        {"id": "type",     "label": "Type",         "emoji": "🎧",
         "options": ["Over-ear", "In-ear (TWS)", "On-ear", "Any"]},
        {"id": "feature",  "label": "Key Feature",  "emoji": "✨",
         "options": ["Noise Cancelling", "Gaming", "Sport / Fitness", "Hi-Fi Audio", "Any"]},
        {"id": "wireless", "label": "Connection",   "emoji": "📡",
         "options": ["Wireless only", "Wired only", "Both OK"]},
        {"id": "brand",    "label": "Brand",        "emoji": "🏷️",
         "options": ["Sony", "Bose", "Apple", "Sennheiser", "Any"]},
    ],
    "camera": [
        {"id": "type",  "label": "Camera Type",    "emoji": "📷",
         "options": ["Mirrorless", "DSLR", "Compact", "Action Cam", "Any"]},
        {"id": "brand", "label": "Brand",          "emoji": "🏷️",
         "options": ["Canon", "Nikon", "Sony", "Fujifilm", "Any"]},
        {"id": "skill", "label": "Skill Level",    "emoji": "⭐",
         "options": ["Beginner", "Intermediate", "Professional", "Any"]},
    ],
    "tv": [
        {"id": "panel",  "label": "Panel Type",    "emoji": "📺",
         "options": ["OLED", "QLED", "LED", "Any"]},
        {"id": "size",   "label": "Screen Size",   "emoji": "📐",
         "options": ["43\"", "55\"", "65\"", "75\"", "Any"]},
        {"id": "brand",  "label": "Brand",         "emoji": "🏷️",
         "options": ["LG", "Samsung", "Sony", "TCL", "Any"]},
    ],
    "drone": [
        {"id": "type",     "label": "Use Case",     "emoji": "🚁",
         "options": ["Photography", "FPV Racing", "Beginner / Toy", "Any"]},
        {"id": "flight",   "label": "Flight Time",  "emoji": "⏱️",
         "options": ["< 20 min", "20–30 min", "30+ min", "Any"]},
        {"id": "brand",    "label": "Brand",        "emoji": "🏷️",
         "options": ["DJI", "Autel", "Holy Stone", "Any"]},
    ],
}

# Pairs: (regex pattern, multiplier) — budget extraction
_BUDGET_PATTERNS = [
    (r'under\s*[₹$€£]?\s*([\d,]+)\s*k\b',  1000),
    (r'under\s*[₹$€£]?\s*([\d,]+)',          1),
    (r'below\s*[₹$€£]?\s*([\d,]+)\s*k\b',  1000),
    (r'below\s*[₹$€£]?\s*([\d,]+)',          1),
    (r'max\s*[₹$€£]?\s*([\d,]+)\s*k\b',    1000),
    (r'budget\s*(?:is\s*)?[₹$€£]?\s*([\d,]+)\s*k\b', 1000),
    (r'budget\s*(?:is\s*)?[₹$€£]?\s*([\d,]+)', 1),
    (r'[₹$€£]\s*([\d,]+)\s*k\b',            1000),
    (r'[₹$€£]\s*([\d,]+)',                    1),
    (r'([\d,]+)\s*k\b',                      1000),
]

_STOP_WORDS = {"i", "want", "a", "an", "the", "need", "looking", "for", "under",
               "below", "above", "is", "my", "budget", "best", "good", "please",
               "with", "and", "or", "some", "any", "get", "buy", "purchase", "find"}


class ShoppingAssistant:
    """
    Parses natural language shopping queries and guides users
    through targeted preference collection before running the full pipeline.
    """

    def parse_query(self, text: str) -> Dict[str, Any]:
        import re
        t = text.lower()

        # Detect most specific category first
        detected = "general"
        for cat, keywords in _CATEGORY_KEYWORDS.items():
            if cat == "general":
                continue
            if any(kw in t for kw in keywords):
                detected = cat
                break

        # Extract budget
        budget: Optional[float] = None
        currency = "USD"
        for pattern, mult in _BUDGET_PATTERNS:
            m = re.search(pattern, t)
            if m:
                budget = float(m.group(1).replace(",", "")) * mult
                if "₹" in text or "inr" in t or "rupee" in t or "lakh" in t:
                    currency = "INR"
                elif "€" in text:
                    currency = "EUR"
                elif "£" in text:
                    currency = "GBP"
                break

        # Build clean search terms
        clean = [w for w in re.sub(r'[₹$€£,]', ' ', t).split()
                 if w not in _STOP_WORDS and not w.replace('.', '').isdigit()]
        search_terms = " ".join(clean[:6])

        return {
            "original":        text,
            "category":        detected,
            "budget":          budget,
            "currency":        currency,
            "search_terms":    search_terms or detected,
            "has_preferences": detected in _PREFERENCE_QUESTIONS,
        }

    def get_preference_questions(self, category: str) -> List[Dict]:
        return _PREFERENCE_QUESTIONS.get(category, [])

    def run_assisted_discovery(
        self,
        query: str,
        preferences: Dict[str, str],
        limit: int = 6,
    ) -> Dict[str, Any]:
        parsed = self.parse_query(query)
        # Enrich search query with selected preference values (skip "Any" answers)
        pref_terms = [v for v in preferences.values()
                      if v and "any" not in v.lower()]
        enriched = " ".join(filter(None, [parsed["search_terms"]] + pref_terms[:3]))

        result = run_pipeline(enriched, limit=limit)
        result["assistant_context"] = {
            "original_query":  query,
            "parsed":          parsed,
            "preferences":     preferences,
            "enriched_query":  enriched,
        }
        return result


# ─── Product Link Analyzer ────────────────────────────────────────────────────

_PLATFORMS = [
    ("amazon.in",     "Amazon India",    "🛒", "INR"),
    ("amazon.com",    "Amazon US",       "🛒", "USD"),
    ("flipkart.com",  "Flipkart",        "🛍️", "INR"),
    ("ebay.com",      "eBay",            "⚡", "USD"),
    ("myntra.com",    "Myntra",          "👔", "INR"),
    ("croma.com",     "Croma",           "⚡", "INR"),
    ("reliancedigital","Reliance Digital","📱", "INR"),
    ("meesho.com",    "Meesho",          "🛒", "INR"),
    ("walmart.com",   "Walmart",         "🏪", "USD"),
    ("bestbuy.com",   "Best Buy",        "💻", "USD"),
    ("newegg.com",    "Newegg",          "🖥️", "USD"),
    ("apple.com",     "Apple Store",     "🍎", "USD"),
    ("snapdeal.com",  "Snapdeal",        "🛒", "INR"),
]

_PLATFORM_MARKUPS: Dict[str, float] = {
    "amazon.in": 1.08, "amazon.com": 1.08, "bestbuy.com": 1.10,
    "apple.com":  1.12, "flipkart.com": 1.05, "croma.com": 1.09,
}


class ProductLinkAnalyzer:
    """
    Analyzes product URLs to extract real product information and find cheaper alternatives.
    Phase 1: Fetches and scrapes the product page for real name/price/specs.
    Phase 2: Searches other stores for the same product to find better deals.
    """

    def detect_platform(self, url: str) -> Dict[str, str]:
        u = url.lower()
        for domain, name, icon, currency in _PLATFORMS:
            if domain in u:
                return {"id": domain, "name": name, "icon": icon, "currency": currency}
        return {"id": "unknown", "name": "Online Store", "icon": "🌐", "currency": "USD"}

    def _url_hints(self, url: str) -> str:
        import re
        # Strip protocol + domain
        path = re.sub(r'https?://[^/]+', '', url).split('?')[0]
        # Remove common path segments and Amazon ASINs
        path = re.sub(r'\b(dp|product|p|item|itm|gp|s|ref|html?|php)\b', ' ', path, flags=re.I)
        path = re.sub(r'\b[A-Z0-9]{10}\b', ' ', path)   # ASIN
        path = re.sub(r'\b\d{5,}\b', ' ', path)          # numeric IDs
        return ' '.join(re.sub(r'[/_\-+%]', ' ', path).split())[:120]

    def analyze_url(self, url: str) -> Dict[str, Any]:
        import re
        platform = self.detect_platform(url)

        # ── Phase 1: Actually scrape the product page ──────────────────────
        scraped = _scrape_product_url(url)

        # ── Extract ASIN for Amazon URLs ───────────────────────────────────
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url.upper())

        # ── Build product name (scraped > URL hints > catalog) ─────────────
        product_name = scraped.get("name", "").strip()

        if not product_name:
            # Fall back to URL path hints matched against mock catalog
            hints = self._url_hints(url).lower()
            discovery = ProductDiscoveryEngine()
            products = discovery.search(hints, limit=1) if hints.strip() else random.sample(_CATALOG[:6], 1)
            fallback_product = products[0] if products else _CATALOG[0]
            product_name = fallback_product.name

        # ── Price: scraped > pipeline search > platform markup estimate ──────
        scraped_price = scraped.get("price")
        # Prefer platform-detected currency for known sites (scraper defaults to USD)
        scraped_currency = scraped.get("currency", "")
        if platform["id"] != "unknown":
            currency = platform["currency"]
        elif scraped_currency and scraped_currency != "USD":
            currency = scraped_currency
        else:
            currency = "INR"

        if scraped_price and scraped_price > 50:
            raw_price = round(float(scraped_price), 2)
            # Convert scraped price to the target currency if different
            scraped_cur = scraped.get("currency", "USD")
            if scraped_cur.upper() != currency.upper():
                platform_price = _convert_currency(raw_price, scraped_cur, currency)
            else:
                platform_price = raw_price
        else:
            # No reliable scraped price — run a quick pipeline search to find market price
            search_name = product_name if product_name else (self._url_hints(url) or "product")
            quick = run_pipeline(search_name, limit=4, currency=currency)
            prices = [l["price"] for l in quick.get("listings", []) if l.get("price", 0) > 0]
            if prices:
                # Use median-ish price as the platform estimate
                prices.sort()
                platform_price = round(prices[len(prices) // 2], 2)
            else:
                # Absolute fallback: catalog mock
                hints = self._url_hints(url).lower()
                discovery = ProductDiscoveryEngine()
                products = discovery.search(hints or product_name, limit=1)
                fallback_product = products[0] if products else _CATALOG[0]
                base_price = _BASE_PRICES.get(fallback_product.id, 500.0)
                markup = _PLATFORM_MARKUPS.get(platform["id"], 1.07)
                platform_price = round(base_price * markup * random.uniform(0.97, 1.04), 2)

        # ── Build category / emoji from scraped name ───────────────────────
        from web_search import _categorize
        category, emoji = _categorize(product_name)

        # ── Build specs ─────────────────────────────────────────────────────
        specs = [
            {"key": "Category",     "value": category},
            {"key": "Condition",    "value": "New"},
            {"key": "Availability", "value": "In Stock" if scraped.get("in_stock", True) else "Check Site"},
        ]
        if scraped.get("rating"):
            specs.append({"key": "Rating", "value": f"{scraped['rating']:.1f} / 5"})
        if scraped.get("review_count"):
            specs.append({"key": "Reviews", "value": f"{scraped['review_count']:,}"})
        if scraped.get("brand"):
            specs.append({"key": "Brand", "value": scraped["brand"]})

        return {
            "name":           product_name,
            "emoji":          emoji,
            "category":       category,
            "description":    scraped.get("description") or f"{category} product from {platform['name']}",
            "image":          scraped.get("image", ""),
            "rating":         scraped.get("rating"),
            "review_count":   scraped.get("review_count", 0),
            "platform":       platform,
            "platform_price": platform_price,
            "currency":       currency,
            "scraped_live":   bool(scraped.get("price")),   # True = real price was scraped
            "asin":           asin_match.group(1) if asin_match else None,
            "original_url":   url,
            "specs":          specs,
        }

    def find_alternatives(
        self,
        product_name: str,
        platform_price: float,
        limit: int = 5,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        result = run_pipeline(product_name, limit=limit, currency=currency)
        for lst in result["listings"]:
            lst["cheaper_than_original"] = lst["price"] < platform_price
            lst["savings"] = round(max(0.0, platform_price - lst["price"]), 2)
        result["cheaper_count"]  = sum(1 for l in result["listings"] if l["cheaper_than_original"])
        result["platform_price"] = platform_price
        result["max_savings"]    = round(
            max((platform_price - l["price"] for l in result["listings"]), default=0), 2
        )
        return result


# Singletons
shopping_assistant    = ShoppingAssistant()
product_link_analyzer = ProductLinkAnalyzer()

