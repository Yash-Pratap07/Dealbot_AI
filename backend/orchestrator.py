"""
Negotiation Engine - DealBot AI  [Web4 Edition]
Full flow per spec:
  User selects product -> Buyer AI generates offer -> Seller AI counters
  -> Evaluator checks fairness -> Strategy switching if stalled
  -> Agreement reached -> Multi-agent signed votes (on-chain)
  -> Autonomous WUSD settlement -> Blockchain record
"""
import asyncio
import time as _time
from typing import AsyncGenerator

from agents import BuyerAgent, SellerAgent
from evaluation import evaluate_deal, BidPayload
from voting import majority_vote_decision
from safety import (
    fraud_check, run_pre_negotiation_checks, detect_adversarial_pattern,
    validate_negotiation_duration, GuardrailViolation,
)
from memory import get_memory_context, save_to_memory

# Web4 imports
try:
    from blockchain.agent_identity import AgentRegistry
    from blockchain.settlement import settle_from_result
    _WEB4_AVAILABLE = True
except ImportError:
    _WEB4_AVAILABLE = False


NEGOTIATION_CONFIG = {
    "maxRounds":            8,
    "agreementThreshold":   50,
    "strategySwitch_round": 3,
    "stallThreshold":       2,
}


async def negotiate_stream(
    max_price,
    min_price,
    strategy="balanced",
    buyer_model="gemini",
    seller_model="gemini",
    market_price=None,
    product="item",
):
    if min_price > max_price:
        min_price, max_price = max_price, min_price
    if market_price is None or market_price <= 0:
        market_price = round((max_price + min_price) / 2, 2)

    memory            = get_memory_context(product)
    buyer             = BuyerAgent(max_budget=max_price, min_price=min_price, strategy=strategy, model=buyer_model)
    seller            = SellerAgent(min_price=min_price, max_price=max_price, strategy=strategy, model=seller_model)
    history           = []
    fraud_flags       = []
    prev_gap          = None
    no_progress       = 0
    strategy_switched = False
    cfg               = NEGOTIATION_CONFIG

    # ── Pre-negotiation guardrails ──────────────────────────────────────
    try:
        pre_checks = run_pre_negotiation_checks(max_price, market_price)
        if pre_checks["warnings"]:
            fraud_flags.extend(pre_checks["warnings"])
    except GuardrailViolation as gv:
        yield {"type": "done", "agreement": False, "final_price": None,
               "evaluation": {"verdict": "BLOCKED", "message": str(gv)},
               "votes": [], "fraud_flags": [str(gv)], "rounds_taken": 0,
               "strategy_switched": False, "memory_hint": memory,
               "history": [], "settlement": None, "agent_identities": []}
        return

    negotiation_start = _time.time()

    for round_num in range(1, cfg["maxRounds"] + 1):

        # ── Time-based abort ───────────────────────────────────────────
        try:
            validate_negotiation_duration(negotiation_start)
        except GuardrailViolation:
            break

        if round_num == cfg["strategySwitch_round"] and not strategy_switched:
            buyer.model  = "GPT"
            seller.model = "Claude"

        if no_progress >= cfg["stallThreshold"] and not strategy_switched:
            buyer.switch_strategy("aggressive")
            seller.switch_strategy("flexible")
            strategy_switched = True

        buyer_price,  buyer_msg  = buyer.make_offer(round_num)
        seller_price, seller_msg = seller.make_counter(round_num)

        # ── Structured BidPayload for audit trail ──────────────────────
        buyer_bid  = BidPayload(price=buyer_price,  days=0, round_num=round_num, agent_role="buyer")
        seller_bid = BidPayload(price=seller_price, days=0, round_num=round_num, agent_role="seller")

        # ── Web4: sign each offer with the agent's wallet ──────────────────
        buyer_sig  = AgentRegistry.sign_offer("buyer_agent",  buyer_price,  round_num) if _WEB4_AVAILABLE else None
        seller_sig = AgentRegistry.sign_offer("seller_agent", seller_price, round_num) if _WEB4_AVAILABLE else None

        # Signed gap: positive = buyer still below seller (normal), negative = buyer crossed seller
        signed_gap = round(seller_price - buyer_price, 2)
        # Display gap is always >= 0
        gap = max(0.0, signed_gap)

        flag = fraud_check(buyer_price, seller_price, market_price)
        if flag:
            fraud_flags.append(flag)

        # ── Adversarial pattern detection ──────────────────────────────
        adv_warning = detect_adversarial_pattern(seller_price, market_price, history)
        if adv_warning:
            fraud_flags.append(adv_warning)

        if prev_gap is not None:
            no_progress = (no_progress + 1) if abs(prev_gap - gap) < 10 else 0
        prev_gap = gap

        round_data = {
            "type": "round", "round": round_num,
            "buyer": buyer_price, "seller": seller_price,
            "buyer_message": buyer_msg, "seller_message": seller_msg,
            "gap": gap, "strategy": buyer.config.strategyType,
            "buyer_model": buyer.model, "seller_model": seller.model,
            "fraud_flag": flag,
            # Structured bid hashes for audit trail
            "buyer_proposal_id":  buyer_bid.proposal_id,
            "seller_proposal_id": seller_bid.proposal_id,
            # Web4: signed offers prove agents made these decisions
            "buyer_agent_address":  buyer_sig["address"]  if buyer_sig  else None,
            "seller_agent_address": seller_sig["address"] if seller_sig else None,
            "buyer_offer_signature":  buyer_sig["signature"]  if buyer_sig  else None,
            "seller_offer_signature": seller_sig["signature"] if seller_sig else None,
        }
        history.append(round_data)
        yield round_data

        # ── Deal close condition ──────────────────────────────────────────
        # 1. Prices have converged within threshold
        # 2. Buyer has crossed above seller (buyer offers more than seller asks)
        #    → close at seller's current ask since buyer is already willing to pay it
        if signed_gap <= cfg["agreementThreshold"]:
            # If buyer crossed seller (buyer_price > seller_price), close at seller's ask
            # Otherwise split the remaining gap fairly
            if buyer_price >= seller_price:
                final_price = seller_price
            else:
                final_price = round((buyer_price + seller_price) / 2, 2)
            evaluation  = evaluate_deal(final_price, market_price)
            votes       = await majority_vote_decision(final_price, market_price, history)
            save_to_memory(product, final_price, buyer.config.strategyType)

            # ── Web4: signed votes + autonomous settlement ─────────────────
            settlement  = None
            vote_result = "ACCEPT"
            if _WEB4_AVAILABLE:
                # Extract vote result from majority vote
                if isinstance(votes, dict):
                    vote_result = votes.get("decision", votes.get("result", "ACCEPT"))
                elif isinstance(votes, list):
                    accept_count = sum(1 for v in votes if (v.get("vote") if isinstance(v, dict) else v) == "ACCEPT")
                    vote_result = "ACCEPT" if accept_count >= 2 else "REJECT"

                done_result = {
                    "agreement": True, "final_price": final_price,
                    "evaluation": evaluation, "votes": votes,
                    "fraud_flags": fraud_flags, "rounds_taken": round_num,
                    "strategy_switched": strategy_switched,
                    "memory_hint": memory, "history": history,
                    "product": product, "vote_result": vote_result,
                }
                settlement = settle_from_result(done_result)

            yield {
                "type": "done", "agreement": True, "final_price": final_price,
                "evaluation": evaluation, "votes": votes,
                "fraud_flags": fraud_flags, "rounds_taken": round_num,
                "strategy_switched": strategy_switched,
                "memory_hint": memory, "history": history,
                # Web4: settlement receipt
                "settlement": settlement,
                "agent_identities": AgentRegistry.all_public() if _WEB4_AVAILABLE else [],
            }
            return

    yield {
        "type": "done", "agreement": False, "final_price": None,
        "evaluation": {"verdict": "NEGOTIATE", "message": "No agreement reached."},
        "votes": [], "fraud_flags": fraud_flags,
        "rounds_taken": cfg["maxRounds"],
        "strategy_switched": strategy_switched,
        "memory_hint": memory, "history": history,
        "settlement": None,
        "agent_identities": AgentRegistry.all_public() if _WEB4_AVAILABLE else [],
    }


async def run_negotiation(
    max_price, min_price,
    strategy="balanced", buyer_model="gemini", seller_model="gemini",
    market_price=None, product="item",
):
    result = {
        "type": "done", "agreement": False, "final_price": None,
        "evaluation": {}, "votes": [], "fraud_flags": [],
        "rounds_taken": 0, "strategy_switched": False,
        "memory_hint": {}, "history": [], "settlement": None,
    }
    async for chunk in negotiate_stream(max_price, min_price, strategy, buyer_model, seller_model, market_price, product):
        if chunk["type"] == "done":
            result = chunk
            break
    return result
