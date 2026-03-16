"""
DEALBOT — Mathematical Agent Logic & Utility Scoring
=====================================================

Implements the utility function from negotiation_protocol.md:

    U(x) = w_p · P(x) + w_t · T(x)

Where:
    - w_p, w_t  are user-assigned importance weights (must sum to 1.0)
    - P(x)      is the normalized price score
    - T(x)      is the normalized timeline score
    - A bid is accepted when U(x) >= threshold (default 0.65)
    - BATNA termination when best offer U < threshold after max rounds

Agents exchange structured bid proposals per the protocol spec.
"""


class DealAgent:
    def __init__(self, role: str, max_budget: float, target_days: int, w_price: float = 0.7, w_time: float = 0.3):
        """
        role: 'buyer' or 'seller'
        max_budget: Absolute maximum the buyer will pay, or minimum the seller will accept.
        target_days: Ideal delivery timeline.
        w_price: Weight for price dimension (default 0.7).
        w_time: Weight for time dimension (default 0.3). Must satisfy w_price + w_time = 1.0.
        """
        self.role = role
        self.max_budget = max_budget
        self.target_days = target_days
        self.w_price = w_price
        self.w_time = w_time

        # The agent will NOT accept any deal below this utility threshold
        self.utility_threshold = 0.65

    def calculate_utility(self, proposed_price: float, proposed_days: int) -> float:
        """
        Core utility function: U(x) = w_p · P(x) + w_t · T(x)

        Returns a float in [0, 1]. Returns 0.0 for dealbreaker proposals.
        """
        # 1. Price Normalization P(x)
        if self.role == 'buyer':
            if proposed_price > self.max_budget:
                return 0.0  # Dealbreaker
            p_score = 1.0 - (proposed_price / self.max_budget)
        else:  # Seller logic
            if proposed_price < self.max_budget:
                return 0.0  # Dealbreaker
            p_score = (proposed_price - self.max_budget) / self.max_budget
            p_score = min(p_score, 1.0)  # Cap at 1.0

        # 2. Time Normalization T(x)
        max_acceptable_days = self.target_days * 2
        if proposed_days > max_acceptable_days:
            return 0.0  # Dealbreaker
        t_score = 1.0 - (proposed_days / max_acceptable_days)

        # 3. Final Utility U(x) = w_p · P(x) + w_t · T(x)
        u_x = (self.w_price * p_score) + (self.w_time * t_score)
        return round(u_x, 4)

    def generate_counter_offer(self, current_price: float, current_days: int):
        """
        Basic concession logic: move 10% closer to the counterparty's offer
        while ensuring it doesn't break the agent's own bounds.
        """
        if self.role == 'buyer':
            new_price = min(current_price * 0.9, self.max_budget)
        else:
            new_price = max(current_price * 1.1, self.max_budget)

        return round(new_price, 2), current_days
