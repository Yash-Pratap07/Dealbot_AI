"""
blockchain/hash_log.py
──────────────────────
Hash negotiation transcripts for a tamper-proof audit trail.

Any change to even a single round — price, order, rounding — produces a
completely different digest, making post-hoc manipulation detectable.
The hash is stored on-chain via DealBotRegistry.recordDeal().
"""

import hashlib
import json


def hash_transcript(history: list[dict]) -> str:
    """
    SHA-256 of the full negotiation history.

    Parameters
    ──────────
    history : list of round dicts, e.g.
              [{"round": 1, "buyer": 500.0, "seller": 900.0}, ...]

    Returns
    ───────
    64-character lowercase hex digest — deterministic for the same input.

    Example
    ───────
    >>> digest = hash_transcript(rounds)
    >>> print(digest)
    'a3f1c9...'
    """
    data = json.dumps(history)
    return hashlib.sha256(data.encode()).hexdigest()


def verify_transcript(history: list[dict], expected_hash: str) -> bool:
    """Return True if recomputed hash matches expected_hash."""
    return hash_transcript(history) == expected_hash
