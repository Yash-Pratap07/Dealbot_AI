"""
blockchain/wusd_transfer.py
────────────────────────────
Transfer WUSD (an ERC-20 token) from the signer account to a recipient.

Environment variables required
───────────────────────────────
  WUSD_ADDRESS  – deployed WUSD ERC-20 token contract address
  WEB3_RPC_URL  – RPC endpoint
  PRIVATE_KEY   – signer private key

The signer must hold sufficient WUSD and ETH (for gas) before calling.
"""

import os
from typing import Any

from .web3_client import get_web3, get_account

# ── Minimal ERC-20 ABI ────────────────────────────────────────────────────────
ERC20_ABI: list[dict] = [
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
        ],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to",     "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _get_token():
    w3      = get_web3()
    address = os.getenv("WUSD_ADDRESS", "")
    if not address:
        raise EnvironmentError("WUSD_ADDRESS is not set in .env")
    return w3.eth.contract(address=w3.to_checksum_address(address), abi=ERC20_ABI)


def get_balance(wallet_address: str) -> float:
    """Return WUSD balance for a wallet address (in token units, not wei)."""
    w3    = get_web3()
    token = _get_token()
    raw   = token.functions.balanceOf(w3.to_checksum_address(wallet_address)).call()
    decimals: int = token.functions.decimals().call()
    return raw / (10 ** decimals)


def transfer_wusd(
    recipient: str,
    amount: float,
) -> dict[str, Any]:
    """
    Transfer `amount` WUSD tokens from the signer to `recipient`.

    Parameters
    ──────────
    recipient  : checksummed Ethereum address of the receiver
    amount     : token amount in human-readable units (e.g. 750.0)

    Returns
    ───────
    dict with tx_hash, block, status, amount_sent
    """
    w3      = get_web3()
    account = get_account()
    token   = _get_token()

    decimals: int = token.functions.decimals().call()
    raw_amount    = int(amount * (10 ** decimals))

    # Sanity-check balance
    balance = token.functions.balanceOf(account.address).call()
    if balance < raw_amount:
        human_bal = balance / (10 ** decimals)
        raise ValueError(
            f"Insufficient WUSD balance: have {human_bal:.4f}, need {amount:.4f}"
        )

    tx = token.functions.transfer(
        w3.to_checksum_address(recipient),
        raw_amount,
    ).build_transaction(
        {
            "from":     account.address,
            "nonce":    w3.eth.get_transaction_count(account.address),
            "gas":      100_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed  = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "tx_hash":     tx_hash.hex(),
        "block":       receipt["blockNumber"],
        "status":      receipt["status"],       # 1 = success, 0 = reverted
        "amount_sent": amount,
        "recipient":   recipient,
    }
