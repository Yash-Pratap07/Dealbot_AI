// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title DealBot AI — Web4 Autonomous Agent Deal Registry
/// @notice Records immutable deal hashes, AI agent votes, and autonomous
///         WUSD settlements. AI agents are first-class on-chain entities.
contract DealBotRegistry {

    // ─── Structs ───────────────────────────────────────────────────────────

    struct Deal {
        address  recorder;
        string   dealHash;
        uint256  finalPrice;      // USD × 100 (cents)
        uint256  timestamp;
        bool     agreement;
        address  buyerWallet;
        address  sellerWallet;
        bool     settled;         // WUSD settlement completed
        bytes32  settlementTx;    // WUSD transfer tx reference
    }

    struct AgentIdentity {
        address  wallet;
        string   agentType;       // "buyer_agent" | "seller_agent" | ...
        string   role;
        uint256  reputation;      // 0-100
        uint256  totalVotes;
        uint256  correctVotes;
        bool     registered;
    }

    struct AgentVote {
        address  agent;
        string   agentType;
        string   vote;            // "ACCEPT" | "REJECT"
        bytes    signature;       // off-chain ECDSA signature
        uint256  confidence;      // 0-100
        uint256  timestamp;
    }

    // ─── State ────────────────────────────────────────────────────────────

    uint256 public dealCount;
    address public platform;      // deployer = platform signer

    mapping(uint256  => Deal)         public deals;
    mapping(uint256  => AgentVote[])  public dealVotes;
    mapping(address  => AgentIdentity) public agents;
    mapping(address  => uint256[])    public userDeals;
    mapping(address  => uint256[])    public agentDeals;

    // ─── Events ───────────────────────────────────────────────────────────

    event DealRecorded(
        uint256 indexed dealId,
        address indexed recorder,
        string  dealHash,
        uint256 finalPrice,
        bool    agreement
    );

    event AgentRegistered(
        address indexed agentWallet,
        string  agentType,
        string  role
    );

    event AgentVoteCast(
        uint256 indexed dealId,
        address indexed agent,
        string  vote,
        uint256 confidence
    );

    event DealSettled(
        uint256 indexed dealId,
        address indexed buyer,
        address indexed seller,
        uint256 amountCents
    );

    event ReputationUpdated(
        address indexed agent,
        uint256 newReputation
    );

    // ─── Modifiers ────────────────────────────────────────────────────────

    modifier onlyPlatform() {
        require(msg.sender == platform, "Only platform can call this");
        _;
    }

    constructor() {
        platform = msg.sender;
    }

    // ─── Agent Registry ───────────────────────────────────────────────────

    /// @notice Register an AI agent as an on-chain identity
    function registerAgent(
        address agentWallet,
        string  calldata agentType,
        string  calldata role
    ) external onlyPlatform {
        agents[agentWallet] = AgentIdentity({
            wallet:       agentWallet,
            agentType:    agentType,
            role:         role,
            reputation:   80,   // starting reputation
            totalVotes:   0,
            correctVotes: 0,
            registered:   true
        });
        emit AgentRegistered(agentWallet, agentType, role);
    }

    // ─── Deal Recording ───────────────────────────────────────────────────

    /// @notice Record a new deal on-chain (called by platform signer)
    function recordDeal(
        string   calldata dealHash,
        uint256  finalPriceCents,
        bool     agreement,
        address  buyerWallet,
        address  sellerWallet
    ) external returns (uint256) {
        uint256 id = dealCount++;
        deals[id] = Deal({
            recorder:     msg.sender,
            dealHash:     dealHash,
            finalPrice:   finalPriceCents,
            timestamp:    block.timestamp,
            agreement:    agreement,
            buyerWallet:  buyerWallet,
            sellerWallet: sellerWallet,
            settled:      false,
            settlementTx: bytes32(0)
        });
        userDeals[msg.sender].push(id);
        if (buyerWallet  != address(0)) userDeals[buyerWallet].push(id);
        if (sellerWallet != address(0)) userDeals[sellerWallet].push(id);
        emit DealRecorded(id, msg.sender, dealHash, finalPriceCents, agreement);
        return id;
    }

    // ─── On-chain Agent Voting ────────────────────────────────────────────

    /// @notice Record an AI agent's signed vote for a deal
    function castAgentVote(
        uint256 dealId,
        address agentWallet,
        string  calldata agentType,
        string  calldata vote,
        bytes   calldata signature,
        uint256 confidence
    ) external onlyPlatform {
        require(dealId < dealCount, "Deal does not exist");
        dealVotes[dealId].push(AgentVote({
            agent:      agentWallet,
            agentType:  agentType,
            vote:       vote,
            signature:  signature,
            confidence: confidence,
            timestamp:  block.timestamp
        }));
        if (agents[agentWallet].registered) {
            agents[agentWallet].totalVotes++;
        }
        agentDeals[agentWallet].push(dealId);
        emit AgentVoteCast(dealId, agentWallet, vote, confidence);
    }

    // ─── Autonomous Settlement ────────────────────────────────────────────

    /// @notice Mark a deal as WUSD-settled (called after ERC-20 transfer)
    function markSettled(
        uint256 dealId,
        bytes32 wusdTxRef
    ) external onlyPlatform {
        require(dealId < dealCount, "Deal does not exist");
        require(deals[dealId].agreement,  "Can only settle agreed deals");
        require(!deals[dealId].settled,   "Already settled");
        deals[dealId].settled      = true;
        deals[dealId].settlementTx = wusdTxRef;
        emit DealSettled(
            dealId,
            deals[dealId].buyerWallet,
            deals[dealId].sellerWallet,
            deals[dealId].finalPrice
        );
    }

    // ─── Reputation Management ────────────────────────────────────────────

    /// @notice Update agent reputation after consensus comparison
    function updateReputation(
        address agentWallet,
        bool    votedCorrectly
    ) external onlyPlatform {
        require(agents[agentWallet].registered, "Agent not registered");
        AgentIdentity storage a = agents[agentWallet];
        if (votedCorrectly) {
            a.correctVotes++;
            a.reputation = a.reputation < 95 ? a.reputation + 1 : 100;
        } else {
            a.reputation = a.reputation > 5 ? a.reputation - 1 : 0;
        }
        emit ReputationUpdated(agentWallet, a.reputation);
    }

    // ─── Views ────────────────────────────────────────────────────────────

    function getUserDeals(address user) external view returns (uint256[] memory) {
        return userDeals[user];
    }

    function getDeal(uint256 id) external view returns (Deal memory) {
        return deals[id];
    }

    function getDealVotes(uint256 id) external view returns (AgentVote[] memory) {
        return dealVotes[id];
    }

    function getAgent(address wallet) external view returns (AgentIdentity memory) {
        return agents[wallet];
    }
}
