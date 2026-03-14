// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title DealExecutor
 * @author Synthetic Minds — IIT Jodhpur
 * @notice On-chain deal settlement for DEALBOT negotiations on WeilChain.
 *         Handles WUSD escrow, approval gates, and milestone-based release.
 *
 * Flow:
 *   1. Buyer calls createDeal() → WUSD locked in escrow
 *   2. Both parties review terms off-chain via Icarus
 *   3. Buyer calls approveDeal() → deal marked approved
 *   4. Seller delivers, buyer calls executeDeal() → WUSD released to seller
 *   5. If dispute: refundDeal() returns WUSD to buyer
 */

interface IWUSD {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract DealExecutor {

    // ---------------------------------------------------------------
    // Data Structures
    // ---------------------------------------------------------------

    enum DealStatus {
        Created,    // Deal created, WUSD in escrow
        Approved,   // Buyer approved the negotiated terms
        Executed,   // WUSD released to seller — deal complete
        Refunded,   // WUSD returned to buyer — deal cancelled
        Disputed    // Under dispute resolution
    }

    struct Deal {
        address buyer;
        address seller;
        uint256 amount;         // WUSD amount
        bytes32 termsHash;      // SHA-256 of canonical deal JSON (from AuditLogger)
        bytes32 auditReceiptId; // On-chain audit receipt reference
        DealStatus status;
        uint256 createdAt;
        uint256 executedAt;
    }

    // ---------------------------------------------------------------
    // State
    // ---------------------------------------------------------------

    IWUSD public immutable wusd;
    mapping(bytes32 => Deal) public deals;
    uint256 public dealCount;

    // ---------------------------------------------------------------
    // Events — logged on-chain for Icarus audit retrieval
    // ---------------------------------------------------------------

    event DealCreated(
        bytes32 indexed dealId,
        address indexed buyer,
        address indexed seller,
        uint256 amount,
        bytes32 termsHash,
        uint256 timestamp
    );

    event DealApproved(
        bytes32 indexed dealId,
        address indexed approvedBy,
        uint256 timestamp
    );

    event DealExecuted(
        bytes32 indexed dealId,
        uint256 amount,
        uint256 timestamp
    );

    event DealRefunded(
        bytes32 indexed dealId,
        uint256 amount,
        uint256 timestamp
    );

    // ---------------------------------------------------------------
    // Constructor
    // ---------------------------------------------------------------

    constructor(address _wusdToken) {
        wusd = IWUSD(_wusdToken);
    }

    // ---------------------------------------------------------------
    // Core Functions
    // ---------------------------------------------------------------

    /**
     * @notice Create a new deal and lock WUSD in escrow.
     * @param _seller     Counterparty wallet address
     * @param _amount     WUSD amount to escrow
     * @param _termsHash  SHA-256 hash of the negotiated terms (from AuditLogger)
     * @param _auditReceiptId  Reference to the on-chain audit receipt
     * @return dealId     Unique identifier for this deal
     */
    function createDeal(
        address _seller,
        uint256 _amount,
        bytes32 _termsHash,
        bytes32 _auditReceiptId
    ) external returns (bytes32) {
        require(_seller != address(0), "Invalid seller address");
        require(_seller != msg.sender, "Cannot deal with yourself");
        require(_amount > 0, "Amount must be positive");

        // Generate unique deal ID
        bytes32 dealId = keccak256(
            abi.encodePacked(msg.sender, _seller, _amount, block.timestamp, dealCount)
        );

        // Transfer WUSD from buyer to this contract (escrow)
        require(
            wusd.transferFrom(msg.sender, address(this), _amount),
            "WUSD transfer failed — check allowance"
        );

        // Store deal
        deals[dealId] = Deal({
            buyer: msg.sender,
            seller: _seller,
            amount: _amount,
            termsHash: _termsHash,
            auditReceiptId: _auditReceiptId,
            status: DealStatus.Created,
            createdAt: block.timestamp,
            executedAt: 0
        });

        dealCount++;

        emit DealCreated(dealId, msg.sender, _seller, _amount, _termsHash, block.timestamp);
        return dealId;
    }

    /**
     * @notice Buyer approves the deal after reviewing terms via Icarus.
     *         This is the human-in-the-loop gate (PS1).
     */
    function approveDeal(bytes32 _dealId) external {
        Deal storage deal = deals[_dealId];
        require(deal.buyer != address(0), "Deal does not exist");
        require(msg.sender == deal.buyer, "Only buyer can approve");
        require(deal.status == DealStatus.Created, "Deal not in Created state");

        deal.status = DealStatus.Approved;

        emit DealApproved(_dealId, msg.sender, block.timestamp);
    }

    /**
     * @notice Execute the deal — release WUSD from escrow to seller.
     *         Called after delivery confirmation.
     */
    function executeDeal(bytes32 _dealId) external {
        Deal storage deal = deals[_dealId];
        require(deal.buyer != address(0), "Deal does not exist");
        require(msg.sender == deal.buyer, "Only buyer can execute");
        require(deal.status == DealStatus.Approved, "Deal not approved");

        deal.status = DealStatus.Executed;
        deal.executedAt = block.timestamp;

        // Release WUSD to seller
        require(
            wusd.transfer(deal.seller, deal.amount),
            "WUSD transfer to seller failed"
        );

        emit DealExecuted(_dealId, deal.amount, block.timestamp);
    }

    /**
     * @notice Refund WUSD to buyer — cancels the deal.
     *         Only callable before execution.
     */
    function refundDeal(bytes32 _dealId) external {
        Deal storage deal = deals[_dealId];
        require(deal.buyer != address(0), "Deal does not exist");
        require(msg.sender == deal.buyer, "Only buyer can refund");
        require(
            deal.status == DealStatus.Created || deal.status == DealStatus.Approved,
            "Cannot refund an executed deal"
        );

        deal.status = DealStatus.Refunded;

        // Return WUSD to buyer
        require(
            wusd.transfer(deal.buyer, deal.amount),
            "WUSD refund failed"
        );

        emit DealRefunded(_dealId, deal.amount, block.timestamp);
    }

    // ---------------------------------------------------------------
    // View Functions — for Icarus audit trail queries
    // ---------------------------------------------------------------

    function getDeal(bytes32 _dealId) external view returns (
        address buyer,
        address seller,
        uint256 amount,
        bytes32 termsHash,
        bytes32 auditReceiptId,
        DealStatus status,
        uint256 createdAt,
        uint256 executedAt
    ) {
        Deal storage deal = deals[_dealId];
        return (
            deal.buyer,
            deal.seller,
            deal.amount,
            deal.termsHash,
            deal.auditReceiptId,
            deal.status,
            deal.createdAt,
            deal.executedAt
        );
    }
}
