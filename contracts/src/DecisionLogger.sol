// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecisionLogger {
    event DecisionLogged(
        bytes32 indexed sessionId,
        bytes32 indexed symbol,
        uint8 action,
        uint8 strategy,
        uint8 confidence,
        int16 pnlBps,
        bytes32 reasoningHash,
        uint256 timestamp
    );

    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function logDecision(
        bytes32 sessionId,
        bytes32 symbol,
        uint8 action,
        uint8 strategy,
        uint8 confidence,
        int16 pnlBps,
        bytes32 reasoningHash
    ) external onlyOwner {
        emit DecisionLogged(sessionId, symbol, action, strategy, confidence, pnlBps, reasoningHash, block.timestamp);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
