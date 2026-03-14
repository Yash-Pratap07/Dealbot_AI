"""
DEALBOT — Unit Tests for DealAgent Utility Scoring
====================================================
"""

import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from evaluation import DealAgent


def test_buyer_utility_within_budget():
    """Buyer should get positive utility when price is below budget."""
    agent = DealAgent(role='buyer', max_budget=400.0, target_days=7)
    utility = agent.calculate_utility(proposed_price=200.0, proposed_days=5)
    assert utility > 0, f"Expected positive utility, got {utility}"
    print(f"  PASS: buyer utility for 200/400 budget = {utility}")


def test_buyer_utility_over_budget():
    """Buyer should get 0 utility when price exceeds budget."""
    agent = DealAgent(role='buyer', max_budget=400.0, target_days=7)
    utility = agent.calculate_utility(proposed_price=500.0, proposed_days=5)
    assert utility == 0.0, f"Expected 0.0, got {utility}"
    print(f"  PASS: buyer utility for price > budget = {utility}")


def test_seller_utility_above_minimum():
    """Seller should get positive utility when price is above minimum."""
    agent = DealAgent(role='seller', max_budget=250.0, target_days=5)
    utility = agent.calculate_utility(proposed_price=350.0, proposed_days=3)
    assert utility > 0, f"Expected positive utility, got {utility}"
    print(f"  PASS: seller utility for 350 > 250 min = {utility}")


def test_seller_utility_below_minimum():
    """Seller should get 0 utility when price below minimum."""
    agent = DealAgent(role='seller', max_budget=250.0, target_days=5)
    utility = agent.calculate_utility(proposed_price=200.0, proposed_days=3)
    assert utility == 0.0, f"Expected 0.0, got {utility}"
    print(f"  PASS: seller utility for price < minimum = {utility}")


def test_timeline_dealbreaker():
    """Utility should be 0 when timeline exceeds 2x target."""
    agent = DealAgent(role='buyer', max_budget=400.0, target_days=7)
    utility = agent.calculate_utility(proposed_price=300.0, proposed_days=15)
    assert utility == 0.0, f"Expected 0.0 for timeline > 2x target, got {utility}"
    print(f"  PASS: timeline dealbreaker (15 > 14) = {utility}")


def test_weights_sum_behavior():
    """Higher price weight should amplify price score impact."""
    agent_price = DealAgent(role='buyer', max_budget=400.0, target_days=7, w_price=0.9, w_time=0.1)
    agent_time = DealAgent(role='buyer', max_budget=400.0, target_days=7, w_price=0.1, w_time=0.9)

    u_price = agent_price.calculate_utility(200.0, 5)
    u_time = agent_time.calculate_utility(200.0, 5)
    assert u_price != u_time, "Different weights should produce different utilities"
    print(f"  PASS: w_price=0.9 → U={u_price}, w_time=0.9 → U={u_time}")


def test_counter_offer_buyer():
    """Buyer counter should decrease the price (multiply by 0.9)."""
    agent = DealAgent(role='buyer', max_budget=400.0, target_days=7)
    new_price, new_days = agent.generate_counter_offer(300.0, 5)
    assert new_price < 300.0, f"Buyer counter should be < 300, got {new_price}"
    assert new_price == 270.0, f"Expected 300*0.9=270, got {new_price}"
    print(f"  PASS: buyer counter 300 → {new_price}")


def test_counter_offer_seller():
    """Seller counter should increase the price (multiply by 1.1)."""
    agent = DealAgent(role='seller', max_budget=250.0, target_days=5)
    new_price, new_days = agent.generate_counter_offer(300.0, 5)
    assert new_price >= 300.0, f"Seller counter should be >= 300, got {new_price}"
    print(f"  PASS: seller counter 300 → {new_price}")


def test_utility_threshold():
    """Utility threshold should be 0.65 by default."""
    agent = DealAgent(role='buyer', max_budget=400.0, target_days=7)
    assert agent.utility_threshold == 0.65, f"Expected 0.65, got {agent.utility_threshold}"
    print(f"  PASS: default threshold = {agent.utility_threshold}")


if __name__ == "__main__":
    print("=" * 50)
    print("DEALBOT — DealAgent Utility Tests")
    print("=" * 50)

    tests = [
        test_buyer_utility_within_budget,
        test_buyer_utility_over_budget,
        test_seller_utility_above_minimum,
        test_seller_utility_below_minimum,
        test_timeline_dealbreaker,
        test_weights_sum_behavior,
        test_counter_offer_buyer,
        test_counter_offer_seller,
        test_utility_threshold,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__} — {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__} — {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'=' * 50}")
