"""
DealBot AI — Payment System
============================
Handles deal payment initiation, completion, and status checks.
Supports: Credit Card, Bank Transfer, Crypto (WUSD), PayPal

Extend this module with a real gateway SDK (Stripe, PayPal, etc.)
without touching any other part of the app.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict

# ─── Models ───────────────────────────────────────────────────────────────────

@dataclass
class PaymentRecord:
    payment_id: str
    deal_id: int
    amount: float
    currency: str
    method: str
    status: str          # pending | completed | failed | refunded
    contract_hash: Optional[str]
    created_at: str
    completed_at: Optional[str] = None
    tx_hash: Optional[str] = None  # blockchain tx hash (crypto payments)
    refunded_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "payment_id":    self.payment_id,
            "deal_id":       self.deal_id,
            "amount":        self.amount,
            "currency":      self.currency,
            "method":        self.method,
            "status":        self.status,
            "contract_hash": self.contract_hash,
            "created_at":    self.created_at,
            "completed_at":  self.completed_at,
            "tx_hash":       self.tx_hash,
            "refunded_at":   self.refunded_at,
        }


# In-memory store — replace with DB-backed table in production
_store: Dict[str, PaymentRecord] = {}

SUPPORTED_METHODS = ["credit_card", "bank_transfer", "crypto_wusd", "paypal"]

_INSTRUCTIONS = {
    "credit_card":    "Enter your card details below to complete the payment securely.",
    "bank_transfer":  "Transfer the amount to: DealBot Bank — Account: DB-8821-4420 — Ref: {payment_id}",
    "crypto_wusd":    "Send {amount} WUSD to DealBot Wallet: 0xDEALB0T000000...CAFE — include Ref: {payment_id}",
    "paypal":         "Pay via PayPal to payments@dealbot.ai — include Ref: {payment_id}",
}

_METHOD_LABELS = {
    "credit_card":   "💳 Credit / Debit Card",
    "bank_transfer": "🏦 Bank Transfer",
    "crypto_wusd":   "🔗 Crypto (WUSD)",
    "paypal":        "🅿️  PayPal",
}

# ─── Payment System ───────────────────────────────────────────────────────────

class PaymentSystem:
    """
    Manages payment lifecycle for completed DealBot deals.

    Usage:
        ps = PaymentSystem()
        result = ps.initiate(deal_id=5, amount=850.00, method="credit_card")
        ps.complete(result["payment_id"])
    """

    def initiate(
        self,
        deal_id: int,
        amount: float,
        method: str,
        contract_hash: Optional[str] = None,
        currency: str = "INR",
    ) -> dict:
        if method not in SUPPORTED_METHODS:
            raise ValueError(f"Unsupported method '{method}'. Choose from: {SUPPORTED_METHODS}")
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")

        pid = f"pay_{uuid.uuid4().hex[:16]}"
        record = PaymentRecord(
            payment_id=pid,
            deal_id=deal_id,
            amount=round(amount, 2),
            currency=currency,
            method=method,
            status="pending",
            contract_hash=contract_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        _store[pid] = record

        instructions = _INSTRUCTIONS[method].format(payment_id=pid, amount=f"{amount:.2f}")
        return {
            "payment_id":   pid,
            "status":       "pending",
            "amount":       record.amount,
            "currency":     currency,
            "method":       method,
            "method_label": _METHOD_LABELS[method],
            "instructions": instructions,
            "deal_id":      deal_id,
            "contract_hash": contract_hash,
        }

    def complete(self, payment_id: str) -> dict:
        record = _get_or_raise(payment_id)
        if record.status != "pending":
            raise ValueError(f"Payment already {record.status}.")
        record.status = "completed"
        record.completed_at = datetime.now(timezone.utc).isoformat()
        # Generate mock blockchain tx hash for crypto payments
        if record.method == "crypto_wusd":
            record.tx_hash = f"0x{uuid.uuid4().hex}"
        return record.to_dict()

    def fail(self, payment_id: str, reason: str = "Payment declined") -> dict:
        record = _get_or_raise(payment_id)
        if record.status != "pending":
            raise ValueError(f"Payment already {record.status}.")
        record.status = "failed"
        record.completed_at = datetime.now(timezone.utc).isoformat()
        return {**record.to_dict(), "failure_reason": reason}

    def refund(self, payment_id: str) -> dict:
        record = _get_or_raise(payment_id)
        if record.status != "completed":
            raise ValueError("Only completed payments can be refunded.")
        record.status = "refunded"
        record.refunded_at = datetime.now(timezone.utc).isoformat()
        return record.to_dict()

    def get_status(self, payment_id: str) -> dict:
        return _get_or_raise(payment_id).to_dict()

    def list_by_deal(self, deal_id: int) -> list:
        return [r.to_dict() for r in _store.values() if r.deal_id == deal_id]


def _get_or_raise(payment_id: str) -> PaymentRecord:
    record = _store.get(payment_id)
    if not record:
        raise ValueError(f"Payment '{payment_id}' not found.")
    return record


# Singleton
payment_system = PaymentSystem()
