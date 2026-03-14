"""
blockchain/contract.py
──────────────────────
Generate deal contracts and interact with the deployed DealBotRegistry
smart contract.

Environment variables required
───────────────────────────────
  CONTRACT_ADDRESS  – deployed DealBotRegistry address
  WEB3_RPC_URL      – RPC endpoint
  PRIVATE_KEY       – signer private key

ABI is inlined here so the module is self-contained; update it if you
recompile DealBotRegistry.sol.
"""

import os
import json
from datetime import datetime, timezone
from typing import Any

from .web3_client import get_web3, get_account

# ── Minimal ABI (only the functions we call) ──────────────────────────────────
REGISTRY_ABI: list[dict] = [
    {
        "inputs": [
            {"internalType": "string",  "name": "dealHash",        "type": "string"},
            {"internalType": "uint256", "name": "finalPriceCents",  "type": "uint256"},
            {"internalType": "bool",    "name": "agreement",        "type": "bool"},
        ],
        "name": "recordDeal",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "getDeal",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "recorder",   "type": "address"},
                    {"internalType": "string",  "name": "dealHash",   "type": "string"},
                    {"internalType": "uint256", "name": "finalPrice", "type": "uint256"},
                    {"internalType": "uint256", "name": "timestamp",  "type": "uint256"},
                    {"internalType": "bool",    "name": "agreement",  "type": "bool"},
                ],
                "internalType": "struct DealBotRegistry.Deal",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserDeals",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _get_contract():
    w3      = get_web3()
    address = os.getenv("CONTRACT_ADDRESS", "")
    if not address:
        raise EnvironmentError("CONTRACT_ADDRESS is not set in .env")
    return w3.eth.contract(address=w3.to_checksum_address(address), abi=REGISTRY_ABI)


def record_deal(
    deal_hash: str,
    final_price: float,
    agreement: bool,
) -> dict[str, Any]:
    """
    Write a deal record to the blockchain.

    Returns a dict with tx_hash and deal_id.
    final_price is in currency units (e.g. 750.00); stored on-chain as cents.
    """
    w3        = get_web3()
    account   = get_account()
    contract  = _get_contract()
    price_cents = int(round(final_price * 100))

    tx = contract.functions.recordDeal(deal_hash, price_cents, agreement).build_transaction(
        {
            "from":  account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas":   200_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed   = account.sign_transaction(tx)
    tx_hash  = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt  = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    # Extract deal ID from logs (first uint256 return value approximation)
    deal_id = int(receipt["logs"][0]["data"].hex(), 16) if receipt["logs"] else None

    return {
        "tx_hash": tx_hash.hex(),
        "block":   receipt["blockNumber"],
        "status":  receipt["status"],          # 1 = success, 0 = reverted
        "deal_id": deal_id,
    }


def get_deal(deal_id: int) -> dict[str, Any]:
    """Fetch a recorded deal by ID (read-only, no gas)."""
    contract = _get_contract()
    d = contract.functions.getDeal(deal_id).call()
    return {
        "recorder":    d[0],
        "deal_hash":   d[1],
        "final_price": d[2] / 100,             # cents → currency units
        "timestamp":   d[3],
        "agreement":   d[4],
    }


def get_user_deals(address: str) -> list[int]:
    """Return all deal IDs recorded by a wallet address."""
    w3       = get_web3()
    contract = _get_contract()
    return contract.functions.getUserDeals(w3.to_checksum_address(address)).call()


def generate_contract(
    buyer: str,
    seller: str,
    price: float,
    transcript_hash: str,
    rounds: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Build a structured contract payload ready for on-chain recording
    or off-chain storage.

    Parameters
    ──────────
    buyer            : buyer identifier (wallet address or agent name)
    seller           : seller identifier
    price            : agreed final price in currency units
    transcript_hash  : SHA-256 hex digest of the negotiation history
    rounds           : optional full round history for audit purposes

    Returns
    ───────
    dict with all contract fields and status "Pending Settlement"
    """
    return {
        "buyer":           buyer,
        "seller":          seller,
        "price":           price,
        "transcript_hash": transcript_hash,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "rounds":          rounds or [],
        "status":          "Pending Settlement",
    }
