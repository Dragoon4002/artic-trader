from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI

from shared.errors import ArticError, ErrorCode, NotFound, register_error_handlers
from shared.models import (
    AgentCreate,
    AgentInfo,
    AgentStatus,
    CloseReason,
    CreditBalance,
    CreditLedgerRow,
    IndexerKind,
    IndexerTags,
    IndexerTxRow,
    LogEntry,
    LogLevel,
    StartRequest,
    StatusResponse,
    StrategyPlan,
    StrategySource,
    Trade,
    TradeSide,
)


def _roundtrip(obj):
    dumped = obj.model_dump(mode="json")
    restored = type(obj).model_validate(dumped)
    assert restored.model_dump(mode="json") == dumped


def test_agent_models_roundtrip():
    now = datetime.now(timezone.utc)
    _roundtrip(AgentCreate(symbol="BTC/USDT"))
    _roundtrip(AgentInfo(id="a1", user_id="u1", symbol="BTC/USDT", status=AgentStatus.RUNNING, created_at=now))
    _roundtrip(StartRequest(agent_id="a1"))
    _roundtrip(StatusResponse(agent_id="a1", status=AgentStatus.STOPPED))


def test_trade_model_roundtrip():
    _roundtrip(
        Trade(
            id="t1",
            agent_id="a1",
            symbol="BTC/USDT",
            side=TradeSide.LONG,
            entry_price=Decimal("100.5"),
            size=Decimal("0.01"),
            opened_at=datetime.now(timezone.utc),
            close_reason=CloseReason.TP,
        )
    )


def test_log_model_roundtrip():
    _roundtrip(LogEntry(agent_id="a1", level=LogLevel.INFO, message="hi", ts=datetime.now(timezone.utc)))


def test_strategy_model_roundtrip():
    _roundtrip(StrategyPlan(id="s1", name="rsi", source=StrategySource.BUILTIN))


def test_credit_models_roundtrip():
    now = datetime.now(timezone.utc)
    _roundtrip(CreditBalance(user_id="u1", balance=Decimal("10"), updated_at=now))
    _roundtrip(CreditLedgerRow(id="c1", user_id="u1", delta=Decimal("-1"), reason="tick", created_at=now))


def test_indexer_models_roundtrip():
    _roundtrip(IndexerTags(chain="eth"))
    _roundtrip(
        IndexerTxRow(
            id="x1",
            kind=IndexerKind.TRADE,
            tx_hash="0xabc",
            block_number=1,
            ts=datetime.now(timezone.utc),
        )
    )


def test_error_codes_and_handlers():
    app = FastAPI()
    register_error_handlers(app)
    err = NotFound("missing", detail={"id": "x"})
    assert err.code == ErrorCode.NOT_FOUND
    assert err.status_code == 404
    shape = err.to_shape()
    assert shape.code == ErrorCode.NOT_FOUND
    assert isinstance(ArticError("boom"), Exception)
