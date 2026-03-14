# DEALBOT: External Market Data via MCP

## Model Context Protocol (MCP) Role
To negotiate effectively, DEALBOT agents need real-time market awareness. Weilliptic's MCP allows our on-chain agents to securely query off-chain APIs without breaking the cryptographic sandbox.

## Required MCP Tools
1. `fetch_market_rate(category, item)`: Queries external web APIs to find the average current market price for a specific service (e.g., freelance graphic design). This establishes the agent's baseline $P(x)$ score.
2. `verify_identity(party_wallet)`: Checks the counterparty's WeilChain history for past successful deals or default rates to adjust risk parameters.

## Implementation Standard
All MCP tool calls must be registered via `icarus.register_mcp_tool()` in the Python backend. The data returned by MCP must be appended to the `AuditLogger` so the user can see *why* the agent accepted a specific price during the final human-in-the-loop approval phase.