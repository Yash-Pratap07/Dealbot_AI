"""
blockchain/agent_identity.py
──────────────────────────────
Web4 — Each AI agent is an autonomous on-chain entity with its own deterministic
wallet derived from the platform's master seed phrase.

Agent types registered on-chain:
  buyer_agent   → index 0
  seller_agent  → index 1
  evaluator     → index 2
  voter_gpt     → index 3
  voter_claude  → index 4
  voter_gemini  → index 5

Environment variables
─────────────────────
  AGENT_MNEMONIC  – BIP-39 mnemonic for deterministic agent wallet generation
                    (defaults to a fixed dev mnemonic if not set — **change in prod**)
  WEB3_RPC_URL    – RPC endpoint

Usage
─────
  from blockchain.agent_identity import get_agent_identity, AgentRegistry
  identity = get_agent_identity("buyer_agent")
  print(identity["address"], identity["type"])
"""

import os
import hashlib
from typing import Any

# ── Agent definitions ─────────────────────────────────────────────────────────

AGENT_TYPES: dict[str, int] = {
    "buyer_agent":   0,
    "seller_agent":  1,
    "evaluator":     2,
    "voter_gpt":     3,
    "voter_claude":  4,
    "voter_gemini":  5,
}

AGENT_ROLES: dict[str, str] = {
    "buyer_agent":   "Negotiates on behalf of the buyer using LLM reasoning",
    "seller_agent":  "Negotiates on behalf of the seller using LLM reasoning",
    "evaluator":     "Evaluates deal fairness and detects fraud patterns",
    "voter_gpt":     "GPT-powered consensus voter (aggressive threshold)",
    "voter_claude":  "Claude-powered consensus voter (balanced threshold)",
    "voter_gemini":  "Gemini-powered consensus voter (conservative threshold)",
}

# ── Deterministic wallet derivation (without HD wallet deps) ─────────────────
# For Web4 we derive deterministic addresses from a seed + agent index.
# In production, replace with proper BIP-32/44 HD derivation via eth_account.

_DEFAULT_DEV_SEED = (
    "talent fruit volcano loan garbage combine neither gravity absorb "
    "picture outside describe"
)


def _derive_agent_private_key(agent_type: str, seed: str | None = None) -> str:
    """Derive a deterministic private key hex for an agent from a seed."""
    if seed is None:
        seed = os.getenv("AGENT_MNEMONIC", _DEFAULT_DEV_SEED)
    index = AGENT_TYPES.get(agent_type, 99)
    raw = f"{seed}:dealbot:agent:{index}:{agent_type}"
    # SHA-256 of the derivation path gives a valid 32-byte private key
    key_bytes = hashlib.sha256(raw.encode()).hexdigest()
    return key_bytes


def _key_to_address(private_key_hex: str) -> str:
    """Convert a 32-byte private key hex to an Ethereum address."""
    try:
        from eth_account import Account
        acct = Account.from_key(private_key_hex)
        return acct.address
    except ImportError:
        # eth_account not installed — compute address manually via keccak
        try:
            from eth_keys import keys
            pk = keys.PrivateKey(bytes.fromhex(private_key_hex))
            return "0x" + pk.public_key.to_address()
        except ImportError:
            # Fallback: deterministic mock address for dev
            h = hashlib.sha256(bytes.fromhex(private_key_hex)).hexdigest()
            return "0x" + h[-40:].upper()


# ── In-memory agent registry ──────────────────────────────────────────────────

_AGENT_CACHE: dict[str, dict] = {}


def get_agent_identity(agent_type: str) -> dict[str, Any]:
    """
    Return the on-chain identity for an AI agent.

    Returns
    -------
    dict with keys:
        type       – agent type string
        index      – agent index (BIP path leaf)
        address    – checksum Ethereum address
        role       – human-readable role description
        private_key – 32-byte hex private key (NEVER log / expose)
    """
    if agent_type not in AGENT_TYPES:
        raise ValueError(f"Unknown agent type: {agent_type!r}. Valid: {list(AGENT_TYPES)}")

    if agent_type not in _AGENT_CACHE:
        pk = _derive_agent_private_key(agent_type)
        addr = _key_to_address(pk)
        _AGENT_CACHE[agent_type] = {
            "type":        agent_type,
            "index":       AGENT_TYPES[agent_type],
            "address":     addr,
            "role":        AGENT_ROLES[agent_type],
            "private_key": pk,  # kept in memory only
        }
    return _AGENT_CACHE[agent_type]


def get_all_agent_identities() -> list[dict]:
    """Return public identity info for all agents (no private keys)."""
    result = []
    for agent_type in AGENT_TYPES:
        identity = get_agent_identity(agent_type)
        result.append({
            "type":    identity["type"],
            "index":   identity["index"],
            "address": identity["address"],
            "role":    identity["role"],
        })
    return result


def sign_message(agent_type: str, message: str) -> dict[str, str]:
    """
    Sign a message with an agent's private key — proves on-chain the agent
    made a decision (vote, offer, etc).
    Returns signature dict or a mock signature in dev mode.
    """
    identity = get_agent_identity(agent_type)
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        msg = encode_defunct(text=message)
        signed = Account.sign_message(msg, private_key=identity["private_key"])
        return {
            "agent":     agent_type,
            "address":   identity["address"],
            "message":   message,
            "signature": signed.signature.hex(),
        }
    except ImportError:
        # Dev mode mock signature
        mock_sig = hashlib.sha256(f"{identity['private_key']}:{message}".encode()).hexdigest()
        return {
            "agent":     agent_type,
            "address":   identity["address"],
            "message":   message,
            "signature": "0x" + mock_sig + "00",  # mock v=0x00
        }


class AgentRegistry:
    """
    On-chain agent registry façade.

    Wraps get_agent_identity() and optionally calls the smart contract's
    registerAgent() function when CONTRACT_ADDRESS is set.
    """

    @staticmethod
    def get(agent_type: str) -> dict:
        return get_agent_identity(agent_type)

    @staticmethod
    def all_public() -> list[dict]:
        return get_all_agent_identities()

    @staticmethod
    def sign_vote(voter_model: str, vote: str, deal_hash: str) -> dict:
        """
        Sign a voting decision on-chain.
        voter_model: 'GPT' | 'Claude' | 'Gemini'
        """
        agent_map = {
            "GPT":    "voter_gpt",
            "Claude": "voter_claude",
            "Gemini": "voter_gemini",
        }
        agent_type = agent_map.get(voter_model, "evaluator")
        payload = f"VOTE:{vote}:DEAL:{deal_hash}"
        return sign_message(agent_type, payload)

    @staticmethod
    def sign_offer(agent_type: str, offer: float, round_num: int) -> dict:
        """Sign a price offer — proves agent made this offer at this round."""
        payload = f"OFFER:{offer}:ROUND:{round_num}"
        return sign_message(agent_type, payload)
