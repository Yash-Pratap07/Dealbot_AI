import random
from dataclasses import dataclass


# ─── Configuration Dataclasses (per spec) ─────────────────────────────────────

@dataclass
class BuyerConfig:
    maxBudget: float
    targetPrice: float
    strategyType: str = "balanced"       # aggressive | balanced | conservative
    patienceLevel: int = 5               # 1-10
    concessionRateBuyer: float = 0.08    # % increase per round


@dataclass
class SellerConfig:
    minPrice: float
    targetPrice: float
    flexibility: float = 0.5             # 0-1
    urgency: float = 0.4                 # 0-1
    concessionRateSeller: float = 0.06   # % decrease per round


# ─── Core Offer Math — exact spec ─────────────────────────────────────────────

def buyer_offer(current_offer: float, config: BuyerConfig) -> float:
    """Start low. Increase slowly. Stop at budget."""
    increase = current_offer * config.concessionRateBuyer
    new_offer = current_offer + increase
    if new_offer > config.maxBudget:
        new_offer = config.maxBudget
    return round(new_offer, 2)


def seller_counter(current_price: float, config: SellerConfig) -> float:
    """Start high. Reduce slowly. Never go below minimum price."""
    reduction = current_price * config.concessionRateSeller
    new_price = current_price - reduction
    if new_price < config.minPrice:
        new_price = config.minPrice
    return round(new_price, 2)


# ─── Psychological Message Templates ─────────────────────────────────────────

_BUYER_POOL = [
    "I appreciate the product quality, but my budget is limited. I can increase my offer slightly to ${offer}.",
    "After careful consideration, I'm willing to raise my bid to ${offer}. This stretches my budget.",
    "I've done my market research — ${offer} reflects the fair value I see here. Can we make this work?",
    "I'm serious about closing this deal. I'm putting ${offer} on the table as a sign of good faith.",
    "I understand your position, but ${offer} is the most I can justify right now.",
    "I'm running low on room. My best reasonable offer is ${offer}.",
    "Please consider ${offer} — it's the maximum I can commit within my budget.",
    "I'd like to move forward. ${offer} is where I see genuine value for both of us.",
]

_BUYER_TACTICS = {
    "aggressive": [
        "I have three other sellers offering similar items. My best is ${offer} — final.",
        "I need this resolved today. ${offer} — take it or leave it.",
        "Prices are falling in the market. ${offer} is generous right now.",
        "I'm walking away unless you accept ${offer}. That's my cap.",
    ],
    "conservative": [
        "I'm very cautious with my budget. ${offer} is where I feel comfortable.",
        "Quality matters to me, but so does value. I can offer ${offer}.",
        "Long-term thinking here — ${offer} makes sense for both sides.",
    ],
    "balanced": [
        "I believe in fair deals. ${offer} works for me if it works for you.",
        "Let's find the middle ground. How about ${offer}?",
        "I'm flexible, but ${offer} is where I see real value today.",
    ],
    "flexible": [
        "I really want to close this. I can go up to ${offer} — my honest best.",
        "Let's not let this fall apart. ${offer} is my revised offer.",
    ],
}

_SELLER_POOL = [
    "This product is premium quality. The best I can do right now is ${price}.",
    "I've invested significantly in this. ${price} reflects its true worth.",
    "Multiple buyers are interested. ${price} is my current offer to you.",
    "The market demand is strong right now. I can come down slightly to ${price}.",
    "Consider the value you're receiving. I can flex to ${price}, but no lower.",
    "${price} covers my cost plus a fair margin. This is a genuine offer.",
    "I appreciate your interest. My best price today is ${price}.",
    "I'll do ${price} to keep this moving — but that's close to my floor.",
]

_SELLER_URGENCY = {
    "high": [
        "I have another offer on the table expiring today. ${price} — first to commit wins.",
        "Limited availability. ${price} — act now or lose this opportunity.",
        "This deal closes tonight. ${price} is where I stand.",
    ],
    "low": [
        "I'm not in a rush, but ${price} is genuinely fair for what you're getting.",
        "Quality like this holds value. ${price} is solid — take your time.",
        "I'll hold at ${price}. The product speaks for itself.",
    ],
}


def generate_buyer_message(offer: float, round_num: int, strategy: str = "balanced") -> str:
    tactics = _BUYER_TACTICS.get(strategy, _BUYER_TACTICS["balanced"])
    pool = (tactics + _BUYER_POOL[:3]) if round_num <= 2 else _BUYER_POOL
    return random.choice(pool).replace("${offer}", f"{offer:,.2f}")


def generate_seller_message(price: float, round_num: int, urgency: float = 0.4) -> str:
    pool = (_SELLER_URGENCY["high"] + _SELLER_POOL[:3]) if urgency > 0.6 else (_SELLER_URGENCY["low"] + _SELLER_POOL)
    return random.choice(pool).replace("${price}", f"{price:,.2f}")


# ─── Rate / Patience Maps ─────────────────────────────────────────────────────

_RATE_BUYER  = {"aggressive": 0.07, "balanced": 0.05, "conservative": 0.03, "flexible": 0.09}
_RATE_SELLER = {"aggressive": 0.07, "balanced": 0.05, "conservative": 0.02, "flexible": 0.09}
_PATIENCE    = {"aggressive": 3,    "balanced": 5,    "conservative": 8}


# ─── Agent Classes ────────────────────────────────────────────────────────────

class BuyerAgent:
    """
    Buyer AI Logic:
      - Start low (60% of budget)
      - Increase slowly via concessionRateBuyer
      - Stop at maxBudget
      - Use psychological tactics
    Config: targetPrice, maxBudget, currentOffer, strategyType, patienceLevel
    """
    def __init__(self, max_budget: float, min_price: float,
                 strategy: str = "balanced", model: str = "gemini"):
        self.config = BuyerConfig(
            maxBudget=max_budget,
            targetPrice=min_price * 1.1,
            strategyType=strategy,
            patienceLevel=_PATIENCE.get(strategy, 5),
            concessionRateBuyer=_RATE_BUYER.get(strategy, 0.08),
        )
        self.model  = model
        # Start at 60% of budget — low opening bid
        self.current_offer = round(max_budget * 0.60, 2)

    def make_offer(self, round_num: int) -> tuple[float, str]:
        self.current_offer = buyer_offer(self.current_offer, self.config)
        msg = generate_buyer_message(self.current_offer, round_num, self.config.strategyType)
        return self.current_offer, msg

    def switch_strategy(self, new_strategy: str) -> None:
        """Called when negotiation stalls — increases aggression."""
        self.config.strategyType     = new_strategy
        self.config.concessionRateBuyer = _RATE_BUYER.get(new_strategy, 0.10)


class SellerAgent:
    """
    Seller AI Logic:
      - Start high (at buyer's max price)
      - Reduce slowly via concessionRateSeller
      - Never go below minPrice
      - Use scarcity tactics
    Config: minPrice, targetPrice, currentPrice, flexibility, urgency
    """
    def __init__(self, min_price: float, max_price: float,
                 strategy: str = "balanced", model: str = "gemini"):
        self.config = SellerConfig(
            minPrice=min_price,
            targetPrice=max_price * 0.9,
            flexibility=({"aggressive": 0.8, "balanced": 0.5, "conservative": 0.2}
                         .get(strategy, 0.5)),
            urgency=({"aggressive": 0.75, "balanced": 0.40, "conservative": 0.20}
                     .get(strategy, 0.40)),
            concessionRateSeller=_RATE_SELLER.get(strategy, 0.06),
        )
        self.model = model
        # Start at buyer's max price — high opening ask
        self.current_price = round(max_price * 1.0, 2)

    def make_counter(self, round_num: int) -> tuple[float, str]:
        self.current_price = seller_counter(self.current_price, self.config)
        msg = generate_seller_message(self.current_price, round_num, self.config.urgency)
        return self.current_price, msg

    def switch_strategy(self, new_strategy: str) -> None:
        """Called when negotiation stalls — increases flexibility."""
        self.config.concessionRateSeller = _RATE_SELLER.get(new_strategy, 0.08)
        self.config.urgency = 0.75 if new_strategy == "flexible" else 0.30
