// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TradeLogger {
    event TradeLogged(
        bytes32 indexed sessionId,   // keccak256(agentId + symbol + timestamp)
        bytes32 indexed symbol,      // keccak256(symbol)
        uint8   side,                // 0=OPEN_LONG, 1=OPEN_SHORT, 2=CLOSE_LONG, 3=CLOSE_SHORT
        uint128 entryPrice,          // scaled by 1e8
        uint128 exitPrice,           // 0 if open event
        int16   pnlBps,             // PnL in basis points (0 if open)
        bytes32 detailHash           // keccak256(JSON of full trade detail)
    );

    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function logTrade(
        bytes32 sessionId,
        bytes32 symbol,
        uint8 side,
        uint128 entryPrice,
        uint128 exitPrice,
        int16 pnlBps,
        bytes32 detailHash
    ) external onlyOwner {
        emit TradeLogged(sessionId, symbol, side, entryPrice, exitPrice, pnlBps, detailHash);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
