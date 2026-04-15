// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DecisionLogger {
    event DecisionLogged(
        bytes32 indexed sessionId,   // keccak256(symbol + agentId + timestamp)
        bytes32 indexed symbol,      // e.g. bytes32("BTCUSD")
        uint8   action,              // 0=HOLD, 1=OPEN_LONG, 2=OPEN_SHORT, 3=CLOSE, 4=ADJUST
        uint8   strategy,            // index into strategy enum
        uint8   confidence,          // 0-100
        int16   pnlBps,             // PnL in basis points
        bytes32 reasoningHash       // keccak256 of full LLM reasoning
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
        emit DecisionLogged(sessionId, symbol, action, strategy, confidence, pnlBps, reasoningHash);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
