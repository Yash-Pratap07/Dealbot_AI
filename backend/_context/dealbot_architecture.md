# DEALBOT × Icarus Integration
**AI That Makes Better Deals for You**
*Synthetic Minds — IIT Jodhpur*

---

## Executive Overview

DEALBOT is an AI-driven negotiation framework integrated with **Icarus** (Weilliptic's agentic chatbot), enabling conversational interfaces for configuring, monitoring, and approving autonomous deal-making workflows on WeilChain.

This integration directly addresses:
- **PS 1** — Human-in-the-Loop Agents (Cerebrum Weil Crate)
- **PS 2** — Agentic Framework with Audit Logging
- **PS 3** — E-Commerce on WeilChain with WUSD Settlement

By combining natural language interaction, cryptographic auditability, and WUSD-based settlement, DEALBOT transforms negotiation into structured, transparent, and enforceable digital intelligence.

---

## Problem Statement

**The world runs on bad deals.**

- Most digital transactions are fixed-price
- Humans negotiate emotionally and inefficiently
- Individuals overpay or undersell
- Businesses lose margin in procurement
- No structured AI-to-AI negotiation layer exists
- No transparent audit trail of how deals are formed

---

## Our Vision — AI as an Economic Actor

| Capability | Description |
|---|---|
| **Represent User Interests** | Act as trusted delegates with clear mandates and boundaries |
| **Negotiate Multi-Round Deals** | Engage in strategic back-and-forth to reach optimal terms |
| **Optimize Outcomes Strategically** | Use utility scoring and risk modeling for best results |
| **Log Reasoning On-Chain** | Transparent audit trail of every decision and proposal |
| **Execute Smart Contracts** | Enforceable agreements with automatic settlement |

> Turning AI from assistant → autonomous deal-maker.

---

## System Objectives

### Structured AI-to-AI Negotiation Engine
- Autonomous agents negotiate prices, terms, and delivery conditions
- Uses predefined negotiation protocols to ensure fair and efficient deal-making
- Reduces manual bargaining and speeds up digital commerce

### Human-in-the-Loop Final Approval
- Final deal requires user confirmation before execution
- Ensures accountability, trust, and control
- Users can review negotiated terms before committing

### Transparent On-Chain Audit Logging
- All negotiation steps are recorded on WeilChain
- Provides tamper-proof and verifiable transaction history
- Ensures transparency for both parties

### Stablecoin-Based Settlement (WUSD)
- Deals settle automatically using WUSD stablecoin
- Enables fast, low-cost, and secure payments
- Eliminates delays in traditional payment systems

---

## System Architecture

**End-to-end flow from user intent to on-chain settlement**

The architecture spans three primary layers:
1. **Conversational Layer** — Icarus chatbot as the natural language front-end
2. **Logic Layer** — DEALBOT autonomous negotiation agents with mandate-bound constraints
3. **Settlement Layer** — WeilChain smart contracts executing WUSD-based deals with on-chain audit receipts

### Inside the DEALBOT Brain
- Intent parsing module extracts structured parameters from natural language
- Utility scoring model ranks counterparty offers against user-defined preferences
- Loop control engine prevents infinite negotiation cycles
- Adversarial detection module guards against manipulation tactics
- Mandate enforcement layer ensures agents never exceed user-set boundaries

---

## Weil SDK Integration

DEALBOT is built directly on the **Weil SDK**, integrating:
- **IcarusClient** — for conversational front-end and user interaction
- **DealBotAgent** — for spawning mandate-bound negotiation agents
- **AuditLogger** — for cryptographically signing and storing every action on-chain
- **MCP Applet Registration** — for connecting external APIs and price feeds as on-chain services
- **WeilChain Smart Contracts** — for enforceable, self-executing deal settlement in WUSD

---

## Trust & Safety Design

| Guardrail | Implementation |
|---|---|
| **User-Defined Boundaries** | Configure negotiation parameters, limits, and constraints before agent activation |
| **No Autonomous Execution** | Explicit approval required before any transaction or contract execution |
| **Cryptographic Logging** | All proposals hashed and signed, creating tamper-evident negotiation records |
| **Loop Control** | Intelligent termination to prevent infinite negotiation cycles and resource waste |
| **Adversarial Handling** | Safeguards against malicious agents, manipulation attempts, and unfair tactics |
| **Transparent Replay** | Complete decision history available for audit, analysis, and dispute resolution |
| **Budget Limits** | Hard-coded max spend per agent instance |
| **Counterparty Whitelist** | Only negotiate with verified WeilChain identities |
| **Time-Based Constraints** | Auto-abort negotiations exceeding 24 hours |
| **Malicious Agent Detection** | Flag unusual patterns (e.g., aggressive lowballing) |
| **User Wallet Confirmation** | Require biometric/2FA for approvals > $10K |

---

## Application Phases of DEALBOT

DEALBOT is designed in progressive application phases:

- **Phase 1 — Core Negotiation Engine:** Single-agent, single-item negotiation with Icarus chat interface and on-chain audit logging
- **Phase 2 — Multi-Agent Orchestration:** Parallel negotiations with multiple counterparties, MCP integration for external APIs, and stress-tested concurrency
- **Phase 3 — Ecosystem Expansion:** Mobile app, ML-based strategy optimization, cross-chain support (Ethereum, Polygon, Solana), and enterprise-grade features

---

## Development Plan

| Phase | Target Date | Key Deliverables |
|---|---|---|
| **MVP Testnet Deployment** | March 10, 2026 | Deploy DEALBOT on WeilChain testnet |
| **Midterm Submission** | March 14, 2026 | Basic Icarus chat interface, single-item negotiation, human-in-the-loop flow, on-chain audit log, demo video |
| **Final Submission** | March 16, 2026 | Multi-party negotiations, MCP integration, preference learning, stress testing (100+ concurrent), full documentation |
| **Post-Hackathon** | Ongoing | Mobile app, ML strategy optimization, cross-chain bridging, enterprise permissions, marketplace API |

---

## 1. What is Icarus?

Icarus is WeilChain's on-chain AI chatbot that transforms natural language commands into secure, policy-bound workflows across enterprise systems. Key capabilities:

- **Natural Language Workflow Orchestration** — Convert plain English prompts into executable, multi-step agent operations
- **MCP (Model Context Protocol) Integration** — Seamlessly connect to external APIs and services deployed as on-chain applets
- **Cryptographic Audit Logging** — Every prompt, tool call, and action is cryptographically signed and immutably logged on WeilChain
- **Serverless Execution** — No infrastructure burden; WeilChain handles sandboxed execution, fault tolerance, and data sovereignty
- **Policy-Bound Security** — Workflows never execute outside defined guardrails; enforces user permissions and constraints

### Why Icarus Matters for DEALBOT
Instead of forcing users to navigate complex negotiation parameters through traditional UIs, Icarus enables conversational configuration: users simply tell DEALBOT what they want to achieve, and the system translates intent into structured negotiation mandates.

---

## 2. Integration Architecture

### 2.1 High-Level Flow

The integration follows this sequence:

1. **User Interaction via Icarus** — User describes negotiation intent in natural language
2. **Intent Parsing & Validation** — Icarus interprets request, validates against user-defined boundaries
3. **DEALBOT Agent Spawning** — System instantiates AI negotiation agents with parsed parameters
4. **Multi-Round Negotiation** — Agents conduct strategic back-and-forth with counterparty agents
5. **Human-in-the-Loop Approval** — Final deal terms presented to user via Icarus for explicit confirmation
6. **On-Chain Settlement** — Upon approval, smart contract executes with WUSD stablecoin payment
7. **Audit Trail Retrieval** — User can query Icarus to retrieve complete negotiation history

### 2.2 Technical Components

| Component | Role | Technology |
|---|---|---|
| Icarus Chatbot | Conversational interface | WeilChain on-chain chatbot |
| Intent Parser | Natural language → structured parameters | LLM-based extraction |
| DEALBOT Agents | Strategic negotiation logic | Autonomous AI agents |
| WeilChain MCP | External API integration layer | Model Context Protocol |
| Audit Logger | Immutable negotiation records | Cryptographic signing + on-chain storage |
| Smart Contracts | Deal execution & settlement | Solidity contracts on WeilChain |
| WUSD Stablecoin | Payment settlement | WeilChain native stablecoin |

---

## 3. Conversational Use Cases

### 3.1 Freelance Service Negotiation

**User Prompt to Icarus:**
> "I need to hire a graphic designer for a logo. My budget is $500-800, deadline is 2 weeks, and I want 3 revision rounds included. Find me the best deal."

**System Response Flow:**
1. Icarus parses intent: Service type (logo design), Budget ($500–$800), Deadline (14 days), Revisions (3 rounds)
2. DEALBOT spawns negotiation agent with these constraints
3. Agent searches marketplace for available designers
4. Conducts multi-round negotiations with 3–5 designer agents
5. Returns top 2 proposals to user via Icarus:
   - **Option A:** $650, 10-day delivery, 4 revisions
   - **Option B:** $720, 7-day delivery, 3 revisions
6. User approves Option A via Icarus chat
7. Smart contract executes; 650 WUSD transferred to escrow
8. Complete negotiation log stored on-chain for dispute resolution

---

### 3.2 B2B Procurement Optimization

**User Prompt to Icarus:**
> "Our company needs 500 units of Product X. Current supplier charges $25/unit. Negotiate with 3 alternative vendors to get the best bulk discount. Must maintain quality standards and accept NET-30 payment terms."

**System Behavior:**
- DEALBOT agent searches WeilChain marketplace for verified Product X suppliers
- Initiates parallel negotiations with 3 vendors
- Uses utility scoring model to weigh price, quality, and payment terms
- Agents propose terms:
  - Vendor 1: $23/unit, NET-30, quality score 4.2/5
  - Vendor 2: $22.50/unit, NET-15, quality score 4.5/5
  - Vendor 3: $24/unit, NET-45, quality score 4.8/5
- DEALBOT ranks by total utility; presents top choice to procurement manager
- Upon approval, 500 units × $22.50 = **11,250 WUSD** locked in smart contract
- Delivery milestones trigger incremental payments

---

### 3.3 Real-Time Market Arbitrage

**User Prompt to Icarus:**
> "Monitor NFT marketplace for Floor Sweep opportunities. If any Bored Ape appears below 30 ETH equivalent in WUSD, negotiate down by 5-10% and auto-purchase if successful. Max budget: 100,000 WUSD."

**System Operation:**
1. DEALBOT subscribes to marketplace event streams via MCP applet
2. When trigger condition met (listing < 30 ETH in WUSD), agent initiates negotiation
3. Agent strategy:
   - Initial offer: 5% below asking
   - If rejected, increment by 1% every 30 seconds
   - Terminate if no acceptance after 10 rounds
4. If deal reached, human-in-the-loop confirmation required before purchase
5. Icarus sends push notification: *"NFT deal found: Bored Ape #1234 at 27,500 WUSD (8% below ask). Approve?"*
6. User confirms; transaction executes on-chain

> **Critical Design Principle: No deal executes without explicit user consent.**

---

## 4. Human-in-the-Loop Implementation

### 4.1 Approval Workflow

**Pre-Negotiation Phase:**
- User sets boundaries via Icarus: *"Never exceed $5,000 per transaction"*
- DEALBOT enforces hard limits at agent level (constraints encoded in agent mandate)
- If negotiation approaches boundary (e.g., $4,800 offer), system flags for early review

**Post-Negotiation Phase:**
1. DEALBOT presents final terms in structured format:
   - Party A: [Your wallet address]
   - Party B: [Counterparty wallet address]
   - Price: X WUSD
   - Delivery Terms: [Details]
   - Penalties/Escrow: [Conditions]
2. User reviews via Icarus chat interface
3. Explicit approval options:
   - **"Approve"** → Executes immediately
   - **"Reject"** → Cancels deal; logs reason on-chain
   - **"Revise"** → User specifies changes; re-enters negotiation
4. Upon approval, cryptographically signed user consent attached to transaction

### 4.2 Safety Guardrails

| Guardrail | Implementation |
|---|---|
| Budget Limits | Hard-coded max spend per agent instance |
| Counterparty Whitelist | Only negotiate with verified WeilChain identities |
| Time-Based Constraints | Auto-abort negotiations exceeding 24 hours |
| Malicious Agent Detection | Flag unusual patterns (e.g., aggressive lowballing) |
| User Wallet Confirmation | Require biometric/2FA for approvals > $10K |

---

## 5. Audit Logging & Transparency

### 5.1 What Gets Logged

Every negotiation step generates an immutable on-chain record:

1. **User Intent** — Original natural language prompt to Icarus
2. **Parsed Parameters** — Structured constraints extracted by system
3. **Agent Spawning** — Timestamp, wallet address, mandate hash
4. **Negotiation Rounds** — Each proposal/counter-proposal with timestamps
5. **Decision Rationale** — Why agent accepted/rejected each offer (utility scores)
6. **Human Approval** — User's signed consent transaction
7. **Settlement** — Smart contract execution, WUSD transfer, final state

### 5.2 Audit Retrieval via Icarus

**User Query:** *"Show me the negotiation history for my logo design deal from last week."*

**Icarus Response:**
```
Deal ID: 0x7a3f...
Date: March 1, 2026, 14:23 IST
Service: Graphic Design (Logo)
Final Price: 650 WUSD
Counterparty: DesignStudio_0x4b2e...

Negotiation Timeline:
[Round 1] Your Agent: 500 WUSD, 3 revisions
[Round 1] Designer Agent: 800 WUSD, 2 revisions
[Round 2] Your Agent: 600 WUSD, 3 revisions
[Round 2] Designer Agent: 750 WUSD, 3 revisions
[Round 3] Your Agent: 650 WUSD, 4 revisions
[Round 3] Designer Agent: ACCEPT

Your Approval: March 1, 2026, 14:31 IST
Status: Completed ✓
WeilChain Receipt: [view on explorer]
```

### 5.3 Dispute Resolution

If conflict arises:
- Both parties can retrieve complete audit trail via Icarus
- Cryptographic signatures prove authenticity of each step
- Independent arbitrators can verify logs without trusting either party
- Smart contract enforces automated refunds if milestones not met

---

## 6. MCP Integration for External Services

### 6.1 Model Context Protocol (MCP) Overview

MCP enables DEALBOT agents to interact with external APIs deployed as WeilChain applets. Examples:
- **Payment Gateways** — Stripe MCP for fiat-to-WUSD conversion
- **Identity Verification** — KYC/AML checks for high-value transactions
- **Shipping APIs** — FedEx/UPS tracking for physical goods deals
- **Credit Scoring** — On-chain reputation systems for counterparty trust
- **Oracle Services** — Real-time price feeds for dynamic negotiations

### 6.2 Example: Dynamic Pricing via Oracle MCP

**Scenario:** User wants to buy 1 Bitcoin at best price across 3 exchanges.

**Flow:**
1. User tells Icarus: *"Buy 1 BTC at best rate under $95,000 equivalent in WUSD"*
2. DEALBOT spawns negotiation agents for Binance, Coinbase, Kraken
3. Agents query PriceFeed_MCP every 10 seconds for live rates:
   - Binance: 94,850 WUSD
   - Coinbase: 95,100 WUSD
   - Kraken: 94,780 WUSD
4. Agent selects Kraken, initiates purchase negotiation
5. Attempts 2% discount: 94,780 × 0.98 = **92,884 WUSD**
6. Kraken agent accepts (liquidity incentive)
7. User approves; 92,884 WUSD transferred via smart contract

---

## 7. Technical Implementation Details

### 7.1 Icarus Chat Integration (Python SDK)

```python
from weil_sdk import IcarusClient, DealBotAgent

# Initialize Icarus client
icarus = IcarusClient(wallet_address="0x...")

# Register DEALBOT agent as MCP applet
dealbot_mcp = icarus.register_mcp(
    applet_name="dealbot_negotiator",
    endpoint="weil://dealbot.applet/negotiate"
)

@icarus.on_message
async def handle_user_prompt(prompt: str):
    # Parse intent using LLM
    intent = parse_negotiation_intent(prompt)

    # Spawn DEALBOT agent with constraints
    agent = DealBotAgent(
        budget_max=intent['budget_max'],
        deadline=intent['deadline'],
        quality_threshold=intent['quality_min']
    )

    # Execute negotiation
    final_deal = await agent.negotiate(marketplace="weilchain_services")

    # Request human approval via Icarus
    approval = await icarus.request_approval(
        deal_summary=final_deal.to_dict(),
        user_wallet=intent['user_wallet']
    )

    if approval.confirmed:
        tx_hash = await agent.execute_deal(final_deal)
        return f"Deal executed! Tx: {tx_hash}"
    else:
        return f"Deal rejected. Reason: {approval.reason}"
```

### 7.2 Audit Logging with WeilChain Receipts

```python
from weil_sdk import AuditLogger

# Initialize logger
logger = AuditLogger(chain="weilchain_mainnet")

@logger.log_action
async def propose_offer(agent_id: str, offer: dict):
    # Log negotiation round — receipt automatically hashed and stored on-chain
    receipt = logger.create_receipt(
        action="propose_offer",
        agent=agent_id,
        data=offer,
        timestamp=datetime.utcnow()
    )
    return receipt.receipt_id
```

### 7.3 Smart Contract Integration

```solidity
// DealExecutor.sol
pragma solidity ^0.8.0;

contract DealExecutor {
    struct Deal {
        address partyA;
        address partyB;
        uint256 amount;
        bytes32 termsHash;
        bool approved;
        bool executed;
    }

    mapping(bytes32 => Deal) public deals;

    function createDeal(
        address _partyB,
        uint256 _amount,
        bytes32 _termsHash
    ) external returns (bytes32) {
        bytes32 dealId = keccak256(
            abi.encodePacked(msg.sender, _partyB, _amount, block.timestamp)
        );
        deals[dealId] = Deal({
            partyA: msg.sender,
            partyB: _partyB,
            amount: _amount,
            termsHash: _termsHash,
            approved: false,
            executed: false
        });
        return dealId;
    }

    function approveDeal(bytes32 _dealId) external {
        Deal storage deal = deals[_dealId];
        require(msg.sender == deal.partyA, "Only party A can approve");
        require(!deal.executed, "Already executed");
        deal.approved = true;
        emit DealApproved(_dealId, block.timestamp);
    }

    function executeDeal(bytes32 _dealId) external {
        Deal storage deal = deals[_dealId];
        require(deal.approved, "Not approved");
        require(!deal.executed, "Already executed");
        // Transfer WUSD stablecoin
        WUSD.transferFrom(deal.partyA, deal.partyB, deal.amount);
        deal.executed = true;
        emit DealExecuted(_dealId, block.timestamp);
    }
}
```

---

## 8. Alignment with Hackathon Problem Statements

### ✅ PS 1: Human-in-the-Loop Agents (Cerebrum Weil Crate)
- Every DEALBOT negotiation requires explicit user approval before execution
- Icarus provides conversational interface for reviewing deal terms
- User can approve, reject, or request modifications at any stage
- Implements step-agent pattern with clear confirmation gates

### ✅ PS 2: Agentic Framework with Audit Logging
- Multi-round agentic negotiation with strategic decision-making
- Every proposal, counter-proposal, and decision logged on-chain
- Cryptographically signed audit trail prevents tampering
- Compatible with external frameworks (LangChain, Google ADK) via MCP

### ✅ PS 3: E-Commerce on WeilChain with WUSD
- Marketplace for services, goods, and digital assets
- All settlements use WUSD stablecoin
- Smart contracts enforce terms automatically
- Escrow, milestone payments, and refunds handled on-chain

---

## 9. Competitive Advantages

### Why DEALBOT + Icarus is Unique

| Feature | Traditional E-Commerce | DEALBOT + Icarus |
|---|---|---|
| Price Discovery | Fixed prices | AI-negotiated optimal prices |
| User Interface | Point-and-click | Natural language |
| Trust | Platform reputation | Cryptographic proofs |
| Transparency | Opaque pricing | Full audit trail |
| Automation | Manual bargaining | Autonomous agents |
| Settlement | Delayed (2–5 days) | Instant (WUSD) |

### Target Markets
1. **Freelance Marketplaces** — Replace Upwork/Fiverr with AI-negotiated contracts
2. **B2B Procurement** — Automate vendor negotiations for enterprises
3. **NFT/Digital Assets** — Intelligent bidding bots for collectors
4. **Real Estate** — Automated offer negotiations between buyers/sellers
5. **Supply Chain** — Dynamic pricing for raw materials and logistics

---

## 10. Implementation Roadmap

### Phase 1 — Midterm Submission (March 14, 2026)
- Basic Icarus chat interface for DEALBOT configuration
- Single-item negotiation (e.g., freelance service deal)
- Human-in-the-loop approval workflow
- On-chain audit logging for 1 complete negotiation
- Demo video: conversational setup → negotiation → approval → settlement

### Phase 2 — Final Submission (March 16, 2026)
- Multi-party negotiations (3+ agents simultaneously)
- MCP integration for external price feeds and identity verification
- Advanced conversational features: deal history queries, preference learning
- Stress testing with 100+ concurrent negotiations
- Comprehensive documentation and deployment guides

### Phase 3 — Post-Hackathon Enhancements
- Mobile app for Icarus chat interface
- Machine learning for agent strategy optimization
- Cross-chain bridging (Ethereum, Polygon, Solana)
- Enterprise features: team permissions, approval hierarchies
- Marketplace API for third-party integrations

---

## 11. Evaluation Criteria Alignment

| Criterion | Weight | How DEALBOT Addresses It |
|---|---|---|
| Innovation | High | First-ever AI-to-AI negotiation framework on blockchain; novel combination of conversational AI + autonomous agents + cryptographic auditability; solves real pain point of inefficient manual bargaining |
| Technical Implementation | High | Clean architecture: Icarus (frontend) ↔ DEALBOT agents (logic) ↔ WeilChain (settlement); robust error handling; loop termination safeguards; production-ready smart contracts |
| Weilliptic SDK Usage | High | Deep integration with Icarus via MCP applets; WeilChain Audit SDK for immutable logging; WUSD stablecoin for all transactions; Cerebrum Weil crate for human-in-the-loop agents |
| On-Chain Integration | High | All negotiation logs stored on WeilChain (not off-chain databases); smart contracts enforce deal terms automatically; cryptographic receipts for every action |
| User Experience | Medium | Conversational interface lowers barrier to entry; clear approve/reject/revise flows with explainable AI decisions; real-time notifications for deal updates |
| Documentation | Medium | This comprehensive technical document; API reference guides for developers; video tutorials for end-users; architecture diagrams and sequence flows |

---

## 12. Conclusion

The DEALBOT × Icarus integration transforms abstract AI negotiation theory into a practical, user-friendly system where anyone can leverage autonomous agents to secure better deals — all through simple conversations.

By combining:
- Icarus's natural language interface
- DEALBOT's strategic negotiation algorithms
- WeilChain's cryptographic auditability
- WUSD stablecoin settlement

We deliver a complete solution addressing all three hackathon problem statements while demonstrating genuine innovation in the Web4 space.

**Next Steps:**
1. Deploy MVP to WeilChain testnet by March 10
2. Record demo video showing end-to-end workflow
3. Submit midterm documentation by March 14
4. Iterate based on mentor feedback
5. Finalize for March 16 submission

> *The future of commerce is conversational, autonomous, and verifiable. DEALBOT + Icarus makes it real.*

---

## References

1. Weilliptic. (2025). Icarus Chatbot Overview. https://weilliptic.ai/icarus
2. Weilliptic. (2024). Web4: Building the Infrastructure for Autonomous, Trustworthy AI. https://weilliptic.ai/blog/web4-building-infrastructure-for-autonomous-trustworthy-ai/
3. Weilliptic. (2026). IIT Mandi Weilliptic Hackathon - Problem Statements. Internal Documentation.
4. Synthetic Minds. (2026). DEALBOT Pitch Deck. IIT Jodhpur Team Submission.
5. Weilliptic Docs. (2025). Integrate MCP Server with Icarus AI Chatbot. https://docs.weilliptic.ai/docs/tutorials/register_mcp/
6. LinkedIn. (2025). Icarus, a chatbot for enterprise data, launches in Public Alpha. https://www.linkedin.com/posts/weilliptic_icarus-started-in-private-alpha-as-a-simple-activity-7373763112254091264-qlDP
7. Weilliptic Docs. (2025). Model Context Protocol (MCP) Integration. https://docs.weilliptic.ai
8. LinkedIn. (2025). How Icarus and WeilChain secure agentic AI with cryptography. https://www.linkedin.com/posts/avinashlakshman_security-and-automation-can-be-achieved-activity-7396265890431983616-e04_
9. Weilliptic. (2026). WeilChain Receipts Part 1: Identity + Verifiable Action Logging for AI Agents. https://weilliptic.ai/blog/weilchain-receipts-part-1/
10. LinkedIn. (2025). Bhavya Bhatt - Weilliptic Chatbot Overview. https://www.linkedin.com/posts/bhavyabhatt_weilliptic-chatbot-activity-7360181538975576064-9fmR
11. LinkedIn. (2025). Icarus chatbot automates finance workflows with compliance and auditability. https://www.linkedin.com/posts/weilliptic_finance-teams-face-a-paradox-theyre-under-activity-7386088334449819648-1M6L
12. Weilliptic Docs. (2025). Step Agent Human-in-the-Loop Tutorial. https://docs.weilliptic.ai/docs/tutorials/step-agent-human-in-the-loop
13. Weilliptic. (2026). WeilChain Audit SDK Documentation. https://docs.weilliptic.ai
14. Weilliptic. (2025). Icarus: Verifiable AI Automation for Enterprise Systems. https://www.linkedin.com/posts/weilliptic_most-enterprise-ai-assistants-today-can-chat-activity-7388629607824093186-ZtbG


