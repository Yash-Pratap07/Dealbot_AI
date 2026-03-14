# DEALBOT: Multi-Agent Negotiation & Utility Logic

## Agent Communication Protocol
DEALBOT agents do not just chat; they exchange structured payloads during a negotiation. 
A standard bid payload includes:
* `proposal_id`: Unique cryptographic hash of the current terms.
* `price`: Proposed amount in WUSD.
* `deliverables`: Array of strictly defined tasks or items.
* `timeline`: Delivery date in UNIX timestamp.

## Utility Scoring Mathematics
Agents evaluate proposals using a weighted utility function. The agent will only accept a deal if the calculated utility $U(x)$ exceeds their minimum reservation threshold.

The core utility formula is:
$$U(x) = w_p \cdot P(x) + w_t \cdot T(x)$$

Where:
* $w_p$ and $w_t$ are the importance weights assigned by the user for Price and Time (must sum to 1.0).
* $P(x)$ is the normalized price score (higher score for lower price if buying).
* $T(x)$ is the normalized timeline score (higher score for faster delivery).

## Loop Control & Termination
* **Max Rounds:** Hardcoded limit of 10 counter-offers per session.
* **BATNA (Best Alternative To a Negotiated Agreement):** If $U(x)$ falls below the threshold after 10 rounds, the agent automatically terminates the negotiation and logs a "No Deal" state on WeilChain.