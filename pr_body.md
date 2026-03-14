## DEALBOT × Icarus — AI-to-AI Negotiation Framework on WeilChain

Autonomous AI agents negotiate prices, terms, and delivery — then settle in WUSD with cryptographic audit trails.

**Team:** Synthetic Minds — IIT Jodhpur

### Key Features
- Multi-agent AI negotiation with utility scoring
- 10-round protocol with BATNA termination
- Human-in-the-loop approval via Icarus
- SHA-256 audit hashing for tamper-proof WeilChain receipts
- WUSD settlement via DealBotRegistry.sol smart contract

### How to Run

```bash
# Backend
pip install fastapi uvicorn websockets web3
cp .env.example .env
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Tests
python tests/test_all_apis.py
```
