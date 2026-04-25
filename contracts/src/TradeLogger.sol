// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TradeLogger {
    event TradeLogged(
        bytes32 indexed sessionId,
        bytes32 indexed symbol,
        uint8 side,
        uint256 entryPrice,
        uint256 exitPrice,
        int16 pnlBps,
        bytes32 detailHash,
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

    function logTrade(
        bytes32 sessionId,
        bytes32 symbol,
        uint8 side,
        uint256 entryPrice,
        uint256 exitPrice,
        int16 pnlBps,
        bytes32 detailHash
    ) external onlyOwner {
        emit TradeLogged(sessionId, symbol, side, entryPrice, exitPrice, pnlBps, detailHash, block.timestamp);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        owner = newOwner;
    }
}
