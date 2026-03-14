"""
DEALBOT — Unit Tests for Preference Learning
==============================================
"""

import sys
import os
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from preferences import PreferenceProfile

def test_preference_initialization():
    profile = PreferenceProfile(initial_w_price=0.7, initial_w_time=0.3)
    assert profile.w_price == 0.7
    assert profile.w_time == 0.3

def test_learning_gradient():
    profile = PreferenceProfile(initial_w_price=0.5, initial_w_time=0.5)

    # Approve 5 very cheap deals (price/budget ratio ~0.2)
    # This should increase price weight
    for _ in range(5):
        profile.record_approval(price=20.0, days=15, budget=100.0)

    # Expected: w_price > w_time because user approves cheap deals
    assert profile.w_price > 0.5
    assert profile.w_time < 0.5
    assert abs(profile.w_price + profile.w_time - 1.0) < 0.001

if __name__ == "__main__":
    tests = [test_preference_initialization, test_learning_gradient]
    for test in tests:
        test()
    print("Preference Tests: PASS")
