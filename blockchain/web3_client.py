"""
blockchain/web3_client.py
─────────────────────────
Web3 connection and signer account.
Set WEB3_RPC_URL in your .env to point at your WeilChain / Hardhat / testnet node.
Set PRIVATE_KEY in your .env for the signer account.
"""

import os
from dotenv import load_dotenv

load_dotenv()

RPC_URL = os.getenv("WEB3_RPC_URL", "")

# Lazy singleton — web3 is only imported and connected on first call
_w3 = None


def get_web3():
    global _w3
    if _w3 is None:
        from web3 import Web3  # deferred import so startup never blocks
        rpc = RPC_URL or "http://127.0.0.1:8545"  # fallback to local hardhat
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 5}))
    return _w3


def get_account():
    """Return an eth_account.Account loaded from PRIVATE_KEY env var."""
    from eth_account import Account  # deferred import
    private_key = os.getenv("PRIVATE_KEY", "")
    if not private_key:
        raise EnvironmentError("PRIVATE_KEY is not set. Add it to your .env file.")
    if not private_key.startswith("0x"):
        private_key = "0x" + private_key
    return Account.from_key(private_key)


def get_chain_id() -> int:
    return get_web3().eth.chain_id
