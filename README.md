# DEALBOT × Icarus — AI That Makes Better Deals for You
### Synthetic Minds — IIT Jodhpur | Weilliptic Hackathon XPECTO'26

> The first AI-to-AI negotiation framework on WeilChain. Autonomous agents negotiate prices, terms, and delivery — then settle in WUSD with cryptographic audit trails.

---

## Problem

Most digital transactions are fixed-price. Humans negotiate emotionally and inefficiently. No structured AI-to-AI negotiation layer exists, and no transparent audit trail shows how deals are formed.

## Solution

DEALBOT transforms negotiation into structured, transparent, and enforceable digital intelligence:

- **AI agents** negotiate autonomously within user-defined mandates
- **Utility scoring** `U(x) = w_p·P(x) + w_t·T(x)` ensures mathematically optimal outcomes
- **10-round protocol** with BATNA termination prevents infinite loops
- **Human-in-the-loop** approval via Icarus before any on-chain execution
- **SHA-256 audit hashing** for tamper-proof WeilChain receipts
- **WUSD settlement** via smart contracts

---

## Architecture

```
┌──────────────────────────────────────────────┐
│  CONVERSATIONAL LAYER                        │
│  Icarus → Intent Parser → @icarus.on_message │
├──────────────────────────────────────────────┤
│  LOGIC LAYER                                 │
│  DealAgent ↔ NegotiationEngine               │
│  MCP Tools ↔ AuditLogger ↔ Guardrails        │
├──────────────────────────────────────────────┤
│  SETTLEMENT LAYER                            │
│  DealBotRegistry.sol → WUSD Escrow → WeilChain│
└──────────────────────────────────────────────┘
```

## Project Structure

```
DEALBOT/
├── backend/
│   ├── blockchain/
│   │   ├── agent_identity.py      # Agent identity management
│   │   ├── contract.py            # Smart contract interaction
│   │   ├── hash_log.py            # SHA-256 audit hash logging
│   │   ├── settlement.py          # On-chain deal settlement
│   │   ├── web3_client.py         # Web3 provider client
│   │   └── wusd_transfer.py       # WUSD token transfers
│   ├── contracts/
│   │   └── DealBotRegistry.sol    # WUSD escrow smart contract
│   ├── _context/                  # Specs & reference docs
│   ├── agents.py                  # Multi-agent definitions
│   ├── auth.py                    # Authentication & sessions
│   ├── database.py                # SQLite database layer
│   ├── evaluation.py              # Deal evaluation metrics
│   ├── llm_router.py              # LLM provider routing
│   ├── main.py                    # FastAPI app + WebSocket endpoints
│   ├── memory.py                  # Conversation memory
│   ├── orchestrator.py            # Multi-agent parallel negotiations
│   ├── payment.py                 # Payment processing logic
│   ├── pipeline.py                # Negotiation pipeline & engine
│   ├── safety.py                  # Safety guardrails & adversarial detection
│   ├── utility.py                 # Utility scoring functions
│   ├── voting.py                  # Agent voting mechanism
│   └── web_search.py              # Web search tool for market data
├── frontend/                      # Next.js React UI
│   ├── src/
│   │   ├── app/                   # Next.js App Router pages
│   │   ├── components/            # React UI components
│   │   ├── context/               # React context providers
│   │   └── lib/                   # Shared utilities
│   └── package.json
├── tests/
│   ├── test_all_apis.py           # Full API test suite
│   ├── test_imports.py            # Import validation
│   ├── test_url_analyze.py        # URL analysis tests
│   ├── test_ws.py                 # WebSocket tests
│   ├── verify_apis.py             # API verification
│   └── web4_test.py               # Web4/blockchain tests
├── static/
│   └── index.html                 # Static landing page
├── logs/                          # Runtime logs
└── .env.example                   # Environment variable template
```

---

## Quick Start

```bash
# 1. Clone & install backend dependencies
pip install fastapi uvicorn websockets web3

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys and config

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Run the FastAPI Backend (Terminal 1)
uvicorn backend.main:app --reload --port 8000

# 5. Run the Next.js Frontend (Terminal 2)
cd frontend
npm run dev

# 6. Run tests
python tests/test_all_apis.py
python tests/test_ws.py
```

---

## How It Works

### 1. User tells Icarus what they want
> *"I need a logo designer, budget $500, delivery in 7 days"*

### 2. DEALBOT parses intent & fetches market data
```python
intent = parse_negotiation_intent(prompt)
market = await icarus.call_mcp_tool("fetch_market_rate", category="freelance_logo_design")
```

### 3. Agents negotiate (max 10 rounds)
```
Round 1: Seller → 600 WUSD    | Buyer U=0.0    → REJECT
Round 1: Buyer  → 360 WUSD    | Seller U=0.55  → REJECT
Round 2: Seller → 396 WUSD    | Buyer U=0.26   → REJECT
...
Round 4: Buyer  → 320 WUSD    | Seller U=0.65  → ACCEPT ✅
```

### 4. Human approves via Icarus
```
Deal: 320 WUSD | 5 days | 4 rounds
Receipt Hash: a7f3b2e1...
→ APPROVE / REJECT / REVISE
```

### 5. Smart contract executes on WeilChain
320 WUSD transferred to escrow → released on delivery confirmation.

---

## Hackathon Alignment

| PS | Description | How DEALBOT Addresses It |
|---|---|---|
| **PS1** | Human-in-the-Loop Agents | `icarus.request_approval()` before any execution |
| **PS2** | Agentic Framework + Audit | Multi-round agents + SHA-256 on-chain logging |
| **PS3** | E-Commerce on WeilChain | WUSD settlement via `DealBotRegistry.sol` |

---

## Weil SDK Integration

| Component | Usage |
|---|---|
| `IcarusClient` | `@icarus.on_message` listener for user prompts |
| `icarus.register_mcp()` | Applet registration as `DEALBOT_v1` |
| `@icarus.register_mcp_tool()` | `fetch_market_rate`, `verify_identity` |
| `AuditLogger` | SHA-256 hashing + `create_receipt()` for on-chain logging |
| `icarus.request_approval()` | Human-in-the-loop approval gate |

---

## Team

**Synthetic Minds** — IIT Jodhpur

---

*The future of commerce is conversational, autonomous, and verifiable. DEALBOT + Icarus makes it real.*
