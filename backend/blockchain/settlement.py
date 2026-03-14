"""
blockchain/settlement.py
──────────────────────────
Web4 — Autonomous deal settlement.

When multi-agent voting reaches majority ACCEPT, this module:
  1. Transfers WUSD from buyer wallet → seller wallet on WeilChain
  2. Records the deal + settlement TX on-chain via DealBotRegistry
  3. Returns a full settlement receipt

This runs WITHOUT human approval — the AI agents are the signers.

Environment variables
─────────────────────
  WEB3_RPC_URL      – RPC endpoint
  PRIVATE_KEY       – platform signer (holds gas ETH for contract calls)
  WUSD_ADDRESS      – WUSD ERC-20 contract
  CONTRACT_ADDRESS  – DealBotRegistry address

Simulation mode
───────────────
When WEB3_RPC_URL is not set / chain is unreachable, settlement returns a
simulated receipt so the rest of the app still works end-to-end.
"""

import os
import time
import hashlib
import secrets
from typing import Any

from .hash_log import hash_transcript
from .agent_identity import AgentRegistry, AGENT_TYPES


# ── Settlement Receipt ────────────────────────────────────────────────────────

def _sim_tx_hash() -> str:
    """Generate a realistic-looking simulated transaction hash."""
    return "0x" + secrets.token_hex(32)


def _sim_address() -> str:
    return "0x" + secrets.token_hex(20)


def _is_chain_available() -> bool:
    """Quick check: is the blockchain configured and reachable?"""
    rpc = os.getenv("WEB3_RPC_URL", "")
    contract = os.getenv("CONTRACT_ADDRESS", "")
    if not rpc or not contract or "YOUR_" in rpc or "YOUR_" in contract:
        return False
    try:
        from .web3_client import get_web3
        w3 = get_web3()
        w3.eth.block_number  # probe
        return True
    except Exception:
        return False


# ── Main settlement function ──────────────────────────────────────────────────

def autonomous_settle(
    deal_hash: str,
    final_price: float,
    buyer_address: str | None,
    seller_address: str | None,
    vote_result: str,        # "ACCEPT" | "REJECT"
    vote_signatures: list[dict],
    history: list[dict],
    product: str = "item",
) -> dict[str, Any]:
    """
    Web4 autonomous settlement.

    Parameters
    ----------
    deal_hash         : SHA-256 hash of negotiation transcript
    final_price       : agreed price (USD float)
    buyer_address     : human buyer's wallet address (MetaMask)
    seller_address    : human seller's wallet address (MetaMask)
                        None = use platform wallet
    vote_result       : majority vote outcome
    vote_signatures   : list of signed vote objects from AgentRegistry
    history           : negotiation round history
    product           : item description

    Returns
    -------
    settlement_receipt dict with all on-chain details
    """
    timestamp = int(time.time())
    price_cents = int(final_price * 100)

    # Build the settlement receipt structure
    receipt: dict[str, Any] = {
        "deal_hash":     deal_hash,
        "product":       product,
        "final_price":   round(final_price, 2),
        "price_cents":   price_cents,
        "vote_result":   vote_result,
        "timestamp":     timestamp,
        "settlement_mode": None,  # "live" | "simulated"
        "wusd_tx_hash":  None,
        "registry_tx_hash": None,
        "deal_id_onchain": None,
        "buyer_address": buyer_address,
        "seller_address": seller_address,
        "agent_signatures": vote_signatures,
        "agents": {
            atype: AgentRegistry.get(atype)["address"]
            for atype in AGENT_TYPES
        },
        "error": None,
    }

    if vote_result != "ACCEPT":
        receipt["settlement_mode"] = "skipped"
        receipt["error"] = "Vote was REJECT — no settlement"
        return receipt

    # ── Attempt live settlement ───────────────────────────────────────────────
    if _is_chain_available():
        try:
            receipt.update(_live_settle(
                deal_hash=deal_hash,
                price_cents=price_cents,
                final_price=final_price,
                buyer_address=buyer_address,
                seller_address=seller_address,
            ))
            receipt["settlement_mode"] = "live"
            return receipt
        except Exception as e:
            receipt["error"] = f"Live settlement failed: {e}; falling back to simulation"

    # ── Simulated settlement (dev / no chain) ────────────────────────────────
    receipt.update(_simulated_settle(deal_hash, price_cents, buyer_address, seller_address))
    receipt["settlement_mode"] = "simulated"
    return receipt


def _live_settle(
    deal_hash: str,
    price_cents: int,
    final_price: float,
    buyer_address: str | None,
    seller_address: str | None,
) -> dict:
    """Execute real on-chain WUSD transfer + registry record."""
    from .web3_client import get_web3, get_account
    from .wusd_transfer import transfer_wusd
    from .contract import record_deal

    w3 = get_web3()
    acct = get_account()
    result = {}

    # WUSD transfer: platform → seller (on behalf of buyer)
    wusd_addr = os.getenv("WUSD_ADDRESS", "")
    if wusd_addr and seller_address:
        tx = transfer_wusd(recipient=seller_address, amount=final_price)
        result["wusd_tx_hash"] = tx.get("tx_hash")
    else:
        result["wusd_tx_hash"] = None

    # Record on DealBotRegistry
    rec = record_deal(deal_hash=deal_hash, final_price=final_price, agreement=True)
    result["registry_tx_hash"]  = rec.get("tx_hash")
    result["deal_id_onchain"]   = rec.get("deal_id")
    return result


def _simulated_settle(
    deal_hash: str,
    price_cents: int,
    buyer_address: str | None,
    seller_address: str | None,
) -> dict:
    """
    Produce a realistic simulated settlement for dev/demo mode.
    All TX hashes and IDs are deterministic from the deal_hash so they
    look consistent across page refreshes.
    """
    seed = deal_hash.encode()
    wusd_tx   = "0x" + hashlib.sha256(seed + b":wusd").hexdigest()
    reg_tx    = "0x" + hashlib.sha256(seed + b":reg").hexdigest()
    deal_id   = int(hashlib.sha256(seed + b":id").hexdigest(), 16) % 10000

    return {
        "wusd_tx_hash":      wusd_tx,
        "registry_tx_hash":  reg_tx,
        "deal_id_onchain":   deal_id,
    }


# ── Reputation scoring ────────────────────────────────────────────────────────

def update_agent_reputation(
    agent_type: str,
    vote: str,
    consensus: str,
    db_session=None,
) -> dict:
    """
    Track whether each agent's vote matched the final consensus.
    Stored in-memory here; in production write to the smart contract.

    Returns new reputation score (0–100).
    """
    correct = (vote == consensus)
    # Placeholder: real impl would call smart contract `updateReputation(agent, +1/-1)`
    return {
        "agent":      agent_type,
        "vote":       vote,
        "consensus":  consensus,
        "correct":    correct,
        "reputation": 85 if correct else 70,  # mock score
        "note": "On-chain reputation updated (simulated in dev mode)",
    }


# ── Convenience: full settle from negotiation result ─────────────────────────

def settle_from_result(
    result: dict,
    buyer_address: str | None = None,
    seller_address: str | None = None,
) -> dict:
    """
    Convenience wrapper called after run_negotiation() completes.

    result   – return value from orchestrator.run_negotiation()
    """
    if not result.get("agreement"):
        return {"settlement_mode": "skipped", "error": "No agreement reached"}

    history    = result.get("history", [])
    deal_hash  = result.get("contract_hash") or hash_transcript(history)
    votes_raw  = result.get("votes", {})
    final_price = result.get("final_price", 0.0)
    product    = result.get("product", "item")
    vote_result = result.get("vote_result", "ACCEPT")

    # Build signed vote objects for each voter
    vote_signatures = []
    if isinstance(votes_raw, dict):
        # votes_raw = {"votes": [...], "decision": ...} from majority_vote_decision
        vote_list = votes_raw.get("votes", [])
        if isinstance(vote_list, list):
            for vote_entry in vote_list:
                if isinstance(vote_entry, dict):
                    model_name = vote_entry.get("model", "unknown")
                    vote_val = vote_entry.get("vote", "UNKNOWN")
                else:
                    model_name = "unknown"
                    vote_val = str(vote_entry)
                sig = AgentRegistry.sign_vote(model_name, vote_val, deal_hash)
                vote_signatures.append(sig)
    elif isinstance(votes_raw, list):
        for vote_entry in votes_raw:
            if isinstance(vote_entry, dict):
                model_name = vote_entry.get("model", "unknown")
                vote_val = vote_entry.get("vote", "UNKNOWN")
            else:
                model_name = "unknown"
                vote_val = str(vote_entry)
            sig = AgentRegistry.sign_vote(model_name, vote_val, deal_hash)
            vote_signatures.append(sig)

    return autonomous_settle(
        deal_hash=deal_hash,
        final_price=final_price,
        buyer_address=buyer_address,
        seller_address=seller_address,
        vote_result=vote_result,
        vote_signatures=vote_signatures,
        history=history,
        product=product,
    )
