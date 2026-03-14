"""
DEALBOT — Unit Tests for Guardrails
=====================================
"""

import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from safety import (
    validate_budget,
    detect_adversarial_pattern,
    GuardrailViolation
)

def test_validate_budget_ok():
    validate_budget(5000.0)  # Should not raise

def test_validate_budget_exceeded():
    try:
        validate_budget(200_000.0) # Limit is 100k
        assert False, "Should have raised violation"
    except GuardrailViolation:
        pass

def test_adversarial_lowball():
    # Offer is 10 WUSD, reference is 100 WUSD (10% < 30% threshold)
    warning = detect_adversarial_pattern(10.0, 100.0, [])
    assert warning is not None
    assert "lowballing" in warning

def test_adversarial_stalling():
    # Same price 3 times
    history = [{"price": 50}, {"price": 50}, {"price": 50}]
    warning = detect_adversarial_pattern(50.0, 100.0, history)
    assert warning is not None
    assert "stalling" in warning

if __name__ == "__main__":
    tests = [test_validate_budget_ok, test_validate_budget_exceeded, test_adversarial_lowball, test_adversarial_stalling]
    for test in tests:
        test()
    print("Guardrails Tests: PASS")
