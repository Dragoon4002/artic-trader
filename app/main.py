# Main entry point for the BNB AI Engine
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .schemas import StartRequest, StatusResponse, PositionSide, StrategyPlan, AIPlannerResponse
from .engine import TradingEngine
from .llm.llm_planner import LLMPlanner
from .log_buffer import clear as clear_log_buffer, get_logs_response
from .llm.chat import chat_completion, CHAT_MODEL_MAP

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path, override=True)
load_dotenv(override=True)

app = FastAPI(title="BNB AI Engine")

# Scheduler for MongoDB cache refresh (when MONGODB_URI is set)
_scheduler = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = TradingEngine()
planner = LLMPlanner()


@app.on_event("startup")
def startup():
    """Initialize MongoDB indexes and start cache refresh scheduler if MONGODB_URI is set and valid."""
    import threading
    global _scheduler
    try:
        from .db import get_db, ensure_indexes
        from .market.cache_refresh import run_refresh
        db = get_db()
        if db is not None:
            ensure_indexes()
            threading.Thread(target=run_refresh, daemon=True).start()
            from apscheduler.schedulers.background import BackgroundScheduler
            from .market.cache_refresh import run_refresh_quotes, run_refresh_historical
            _scheduler = BackgroundScheduler()
            # Quotes (CMC + Pyth): every 60 seconds (1 minute)
            _scheduler.add_job(run_refresh_quotes, "interval", seconds=60, id="cache_refresh_quotes")
            # Historical (Twelve Data): every 10 minutes to stay under API rate limit
            _scheduler.add_job(run_refresh_historical, "interval", seconds=600, id="cache_refresh_historical")
            _scheduler.start()
            print("[Startup] MongoDB cache enabled: quotes every 60s, historical every 10 min.")
        else:
            uri = (os.getenv("MONGODB_URI") or "").strip()
            if uri and "xxxxx" not in uri:
                print("[Startup] MongoDB connection failed. Check MONGODB_URI in .env; using third-party APIs until fixed.")
            else:
                print("[Startup] MONGODB_URI not set or placeholder. Set a valid Atlas URL in .env to serve data from MongoDB.")
    except Exception as e:
        print(f"[Startup] MongoDB cache disabled: {e}")


@app.on_event("shutdown")
def shutdown():
    """Stop cache refresh scheduler."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


# ---------- Basic API Endpoints ----------

@app.get("/health")
def health():
    """Health check. Returns ok and whether the engine is running."""
    return {"ok": True, "running": engine.is_alive()}


@app.post("/plan", response_model=StrategyPlan)
async def plan(req: StartRequest):
    """
    Get AI-generated strategy plan without starting a trading session.
    Analyzes market data and returns the strategy the AI would use.
    """
    from .market.market import MarketData

    twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not twelve_data_api_key:
        raise HTTPException(status_code=500, detail="TWELVE_DATA_API_KEY not set")

    market_data = MarketData(twelve_data_api_key=twelve_data_api_key)
    current_price = market_data.get_price_with_retry(req.symbol)
    if current_price is None:
        raise HTTPException(status_code=502, detail=f"Failed to fetch price for {req.symbol}")

    market_summary = market_data.get_market_summary(req.symbol)
    market_context = {
        "current_price": current_price,
        "symbol": req.symbol,
        "market_summary": market_summary,
    }

    _raw = (req.llm_provider or "").strip().lower()
    llm_provider_param = _raw if _raw in ("openai", "anthropic", "deepseek", "gemini") else None

    return planner.plan_strategy(
        symbol=req.symbol,
        amount_usdt=req.amount_usdt,
        leverage=req.leverage,
        risk_profile=req.risk_profile or "moderate",
        primary_timeframe=req.primary_timeframe or "15m",
        market_context=market_context,
        llm_provider=llm_provider_param,
        indicators=req.indicators,
    )


@app.post("/ai-planner", response_model=AIPlannerResponse)
async def ai_planner(req: StartRequest):
    """
    Full AI planner analysis:
    - Market regime summary
    - Strategy plan with parameters
    - Strategy shortlist
    - Analysis paragraph and quant algo description
    """
    from .market.market import MarketData

    twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not twelve_data_api_key:
        raise HTTPException(status_code=500, detail="TWELVE_DATA_API_KEY not set")

    market_data = MarketData(twelve_data_api_key=twelve_data_api_key)
    current_price = market_data.get_price_with_retry(req.symbol)
    if current_price is None:
        raise HTTPException(status_code=502, detail=f"Failed to fetch price for {req.symbol}")

    market_summary = market_data.get_market_summary(req.symbol)
    market_context = {
        "current_price": current_price,
        "symbol": req.symbol,
        "market_summary": market_summary,
    }

    _raw = (req.llm_provider or "").strip().lower()
    llm_provider_param = _raw if _raw in ("openai", "anthropic", "deepseek", "gemini") else None

    try:
        summary, strategy_plan, strategy_shortlist, analysis_paragraph, quant_algo_description = (
            planner.get_full_analysis(
                symbol=req.symbol,
                amount_usdt=req.amount_usdt,
                leverage=req.leverage,
                risk_profile=req.risk_profile or "moderate",
                primary_timeframe=req.primary_timeframe or "15m",
                market_context=market_context,
                llm_provider=llm_provider_param,
                indicators=req.indicators,
            )
        )
    except Exception as e:
        err_str = str(e).lower()
        if "401" in err_str or "invalid_api_key" in err_str or "authentication" in err_str or "incorrect api key" in err_str:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "llm_auth_failed",
                    "message": "LLM API key rejected. Check OPENAI_API_KEY, ANTHROPIC_API_KEY, or DEEPSEEK_API_KEY in .env",
                },
            ) from e
        raise

    return AIPlannerResponse(
        symbol=req.symbol,
        primary_timeframe=req.primary_timeframe or "15m",
        bar_count_used=summary.bar_count_used,
        market_regime_summary=summary,
        strategy_plan=strategy_plan,
        strategy_shortlist=strategy_shortlist,
        analysis_paragraph=analysis_paragraph,
        quant_algo_description=quant_algo_description,
    )


@app.post("/start")
async def start(req: StartRequest):
    """Start a paper trading session (non-blocking: returns immediately, engine initializes in background)."""
    clear_log_buffer()
    _raw = (req.llm_provider or "").strip().lower()
    llm_provider_param = _raw if _raw in ("openai", "anthropic", "deepseek", "gemini") else None

    import asyncio

    asyncio.create_task(engine.start(
        symbol=req.symbol,
        amount_usdt=req.amount_usdt,
        leverage=req.leverage,
        poll_seconds=req.poll_seconds,
        tp_pct=req.tp_pct,
        sl_pct=req.sl_pct,
        risk_profile=req.risk_profile or "moderate",
        primary_timeframe=req.primary_timeframe or "15m",
        live_mode=req.live_mode or False,
        tp_sl_mode=req.tp_sl_mode or "fixed",
        supervisor_interval_seconds=req.supervisor_interval_seconds or 60.0,
        llm_provider=llm_provider_param,
        indicators=req.indicators,
    ))
    return {
        "started": True,
        "symbol": req.symbol,
        "live_mode": req.live_mode or False,
        "tp_sl_mode": req.tp_sl_mode or "fixed",
        "supervisor_interval_seconds": req.supervisor_interval_seconds or 60.0,
    }


class ConfigUpdateRequest(BaseModel):
    amount_usdt: Optional[float] = None
    tp_pct: Optional[float] = None
    sl_pct: Optional[float] = None
    tp_sl_mode: Optional[str] = None
    supervisor_interval_seconds: Optional[float] = None
    poll_seconds: Optional[float] = None
    risk_profile: Optional[str] = None


@app.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """Hot-reload non-critical config into running engine. Changes apply on next tick."""
    if not engine or not engine.running:
        raise HTTPException(status_code=400, detail="Engine not running")

    if request.amount_usdt is not None:
        engine.amount_usdt = request.amount_usdt
    if request.tp_pct is not None:
        engine.tp_pct = request.tp_pct
        if engine.position.side != PositionSide.FLAT:
            engine.position.tp_pct = request.tp_pct
    if request.sl_pct is not None:
        engine.sl_pct = request.sl_pct
        if engine.position.side != PositionSide.FLAT:
            engine.position.sl_pct = request.sl_pct
    if request.tp_sl_mode is not None:
        engine._tp_sl_mode = request.tp_sl_mode
    if request.supervisor_interval_seconds is not None:
        engine._supervisor_interval_seconds = request.supervisor_interval_seconds
    if request.poll_seconds is not None:
        engine.poll_seconds = request.poll_seconds

    from .log_buffer import emit as _emit
    _emit("init", f"[CONFIG] Hot-reloaded: {request.model_dump(exclude_none=True)}")
    return {"status": "ok", "updated": request.model_dump(exclude_none=True)}


@app.post("/stop")
async def stop(closePosition: bool = True):
    """Stop the trading session. Optionally close the current position."""
    await engine.stop(close_position=closePosition)
    return {"stopped": True, "closed": closePosition}


@app.get("/status", response_model=StatusResponse)
def status():
    """Get current trading status."""
    price_for_pnl = engine.last_price
    if engine.position.side != PositionSide.FLAT and engine.symbol and engine.market_data:
        try:
            fresh = engine.market_data.get_price_with_retry(engine.symbol)
            if fresh is not None:
                price_for_pnl = fresh
        except Exception:
            pass
    unrealized_pnl = None
    if price_for_pnl is not None and engine.position.side != PositionSide.FLAT:
        unrealized_pnl = engine.position.unrealized_pnl(price_for_pnl)
    active_strategy = engine.strategy_plan.strategy if engine.strategy_plan else None

    return StatusResponse(
        running=engine.is_alive(),
        symbol=engine.symbol,
        last_price=price_for_pnl if price_for_pnl is not None else engine.last_price,
        amount_usdt=engine.amount_usdt,
        config_leverage=engine.leverage,
        side=engine.position.side,
        entry_price=engine.position.entry_price,
        position_size_usdt=engine.position.size_usdt,
        leverage=engine.position.leverage,
        unrealized_pnl_usdt=unrealized_pnl,
        last_action=engine.last_action,
        last_reason=engine.last_reason,
        active_strategy=active_strategy,
    )


# ---------- Copilot Chat API ----------


@app.post("/chat")
async def chat(req: dict):
    """
    Copilot chat: accepts { messages: [...], model: "<model-id>" }.
    Routes to OpenAI, Claude, or DeepSeek based on model ID.
    """
    try:
        messages = req.get("messages")
        model_id = (req.get("model") or "claude-sonnet-4-5").strip()
        if not isinstance(messages, list) or len(messages) == 0:
            raise HTTPException(
                status_code=400,
                detail="messages array is required and must not be empty",
            )
        last = messages[-1] if messages else {}
        if last.get("role") != "user":
            raise HTTPException(
                status_code=400,
                detail="Last message must be from user",
            )
        if model_id not in CHAT_MODEL_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model: {model_id}. Supported: {list(CHAT_MODEL_MAP.keys())}",
            )
        reply = chat_completion(messages=messages, model_id=model_id)
        return {"message": reply}
    except HTTPException:
        raise
    except ValueError as e:
        err_str = str(e).lower()
        if "api key" in err_str or "not set" in err_str:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "llm_config",
                    "message": str(e),
                },
            ) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail={
                "error": "chat_failed",
                "message": str(e),
            },
        ) from e


@app.get("/chat/models")
def chat_models():
    """Return available chat model options for the Copilot dropdown."""
    models = [
        {"id": k, "name": _model_display_name(k), "provider": v[0]}
        for k, v in CHAT_MODEL_MAP.items()
    ]
    return {"models": models}


def _model_display_name(model_id: str) -> str:
    names = {
        "gpt-4o": "GPT-4o",
        "gpt-4o-mini": "GPT-4o Mini",
        "gpt-4-turbo": "GPT-4 Turbo",
        "claude-sonnet-4-5": "Claude Sonnet 4.5",
        "claude-3-5-sonnet": "Claude 3.5 Sonnet",
        "claude-3-5-haiku": "Claude 3.5 Haiku",
        "deepseek-chat": "DeepSeek Chat",
        "deepseek-reasoner": "DeepSeek Reasoner",
        "deepseek-r1": "DeepSeek R1",
    }
    return names.get(model_id, model_id)


@app.get("/logs")
def logs():
    """Return live AI engine logs for frontend display."""
    return get_logs_response(engine.is_alive())


# ---------- Market Data APIs ----------

@app.get("/historical-data")
async def get_historical_data(symbol: str = "BTCUSDT", days: int = 30):
    """Get historical price data from Twelve Data."""
    from .market.market import MarketData

    twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not twelve_data_api_key:
        return {"error": "TWELVE_DATA_API_KEY not set"}

    market_data = MarketData(twelve_data_api_key=twelve_data_api_key)
    try:
        historical = market_data.get_historical_data(symbol, days=min(days, 5000))
        if not historical:
            return {
                "success": False,
                "symbol": symbol,
                "days_requested": days,
                "count": 0,
                "data": [],
                "error": "Failed to fetch historical data",
            }
        return {
            "success": True,
            "symbol": symbol,
            "days_requested": days,
            "count": len(historical),
            "data": historical,
            "summary": {
                "first_date": historical[0]["date"] if historical else None,
                "last_date": historical[-1]["date"] if historical else None,
                "price_range": {
                    "min": min(d["price"] for d in historical) if historical else None,
                    "max": max(d["price"] for d in historical) if historical else None,
                    "first": historical[0]["price"] if historical else None,
                    "last": historical[-1]["price"] if historical else None,
                    "change": (historical[-1]["price"] - historical[0]["price"]) if len(historical) > 0 else None,
                    "change_pct": ((historical[-1]["price"] - historical[0]["price"]) / historical[0]["price"] * 100)
                    if len(historical) > 0 and historical[0]["price"] > 0
                    else None,
                },
            },
        }
    except Exception as e:
        return {"success": False, "symbol": symbol, "days_requested": days, "count": 0, "data": [], "error": str(e)}


@app.get("/candles")
async def get_candles(symbol: str = "BTCUSDT", timeframe: str = "15m", limit: int = 100):
    """Get OHLCV candles from Twelve Data."""
    from .market.market import MarketData

    twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not twelve_data_api_key:
        return {"error": "TWELVE_DATA_API_KEY not set"}

    limit = min(limit, 1000)
    market_data = MarketData(twelve_data_api_key=twelve_data_api_key)

    try:
        candles = market_data.get_ohlcv_candles(symbol, timeframe, limit)
        if not candles:
            return {
                "success": False,
                "symbol": symbol,
                "timeframe": timeframe,
                "count": 0,
                "candles": [],
                "error": "Failed to fetch candles",
            }
        candle_list = [
            {
                "index": i,
                "timestamp": str(c.timestamp),
                "timestamp_iso": c.timestamp.isoformat(),
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
                "change": c.close - c.open,
                "change_pct": ((c.close - c.open) / c.open * 100) if c.open > 0 else 0,
                "range": c.high - c.low,
                "range_pct": ((c.high - c.low) / c.open * 100) if c.open > 0 else 0,
                "body": abs(c.close - c.open),
                "upper_wick": c.high - max(c.open, c.close),
                "lower_wick": min(c.open, c.close) - c.low,
            }
            for i, c in enumerate(candles)
        ]
        if candle_list:
            closes = [c["close"] for c in candle_list]
            volumes = [c["volume"] for c in candle_list]
            summary = {
                "first_candle_time": candle_list[0]["timestamp"],
                "last_candle_time": candle_list[-1]["timestamp"],
                "price_range": {
                    "min": min(closes),
                    "max": max(closes),
                    "current": closes[-1],
                    "change_from_first": closes[-1] - closes[0],
                    "change_pct_from_first": ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] > 0 else 0,
                },
                "volume_stats": {
                    "total": sum(volumes),
                    "average": sum(volumes) / len(volumes) if volumes else 0,
                    "min": min(volumes) if volumes else 0,
                    "max": max(volumes) if volumes else 0,
                },
            }
        else:
            summary = None
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(candle_list),
            "summary": summary,
            "candles": candle_list,
        }
    except Exception as e:
        return {"success": False, "symbol": symbol, "timeframe": timeframe, "count": 0, "candles": [], "error": str(e)}


# ---------- Explore (Forex / Crypto) ----------

FOREX_SYMBOLS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "USD/CAD", "NZD/USD",
    "USD/INR", "EUR/GBP", "EUR/JPY", "GBP/JPY", "CHF/JPY", "EUR/CHF", "AUD/JPY",
    "EUR/AUD", "GBP/AUD", "CAD/JPY", "AUD/NZD", "EUR/NZD", "GBP/CHF",
]
CRYPTO_SYMBOLS = [
    "BTC/USD", "ETH/USD", "BNB/USD", "XRP/USD", "SOL/USD", "ADA/USD", "DOGE/USD",
    "AVAX/USD", "DOT/USD", "MATIC/USD", "LINK/USD", "UNI/USD", "ATOM/USD",
    "LTC/USD", "ETC/USD", "XLM/USD", "BCH/USD", "NEAR/USD", "APT/USD", "ARB/USD",
]
QUOTE_BATCH_SIZE = 8


def _normalize_quote(raw: dict) -> dict:
    def f(key: str, default=None):
        v = raw.get(key)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default
    return {
        "symbol": raw.get("symbol", ""),
        "name": raw.get("name", raw.get("symbol", "")),
        "open": f("open"),
        "high": f("high"),
        "low": f("low"),
        "close": f("close"),
        "volume": f("volume", 0) or 0,
        "previous_close": f("previous_close"),
        "change": f("change"),
        "percent_change": f("percent_change"),
    }


def _parse_batch_quote_response(data, expected_symbols: list) -> list:
    out = []
    if not data:
        return out
    if isinstance(data, dict) and data.get("status") == "error":
        return out
    if isinstance(data, dict) and data.get("symbol"):
        out.append(_normalize_quote(data))
        return out
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("symbol"):
                out.append(_normalize_quote(item))
        return out
    if isinstance(data, dict) and "data" in data:
        arr = data["data"]
        if isinstance(arr, list):
            for item in arr:
                if isinstance(item, dict) and item.get("symbol"):
                    out.append(_normalize_quote(item))
        return out
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict) and (val.get("symbol") or key):
                raw = dict(val) if val.get("symbol") else {**val, "symbol": key}
                if raw.get("symbol"):
                    out.append(_normalize_quote(raw))
        return out
    return out


def _fetch_quotes_batch(symbols: list, api_key: str) -> list:
    if not symbols or not api_key:
        return []
    url = "https://api.twelvedata.com/quote"
    symbol_param = ",".join(symbols)
    params = {"symbol": symbol_param, "apikey": api_key, "format": "JSON", "interval": "1day"}
    try:
        r = requests.get(url, params=params, timeout=25)
        if r.status_code == 414:
            return _fetch_quotes_batch_chunked(symbols, api_key)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.HTTPError as e:
        print(f"[Explore] Twelve Data HTTP error: {e}")
        return _fetch_quotes_batch_chunked(symbols, api_key)
    except Exception as e:
        print(f"[Explore] Twelve Data request failed: {e}")
        return []
    parsed = _parse_batch_quote_response(data, symbols)
    if len(parsed) < min(3, len(symbols)):
        return _fetch_quotes_batch_chunked(symbols, api_key)
    return parsed


def _fetch_quotes_batch_chunked(symbols: list, api_key: str) -> list:
    if not symbols or not api_key:
        return []
    url = "https://api.twelvedata.com/quote"
    all_quotes = []
    for i in range(0, len(symbols), QUOTE_BATCH_SIZE):
        chunk = symbols[i : i + QUOTE_BATCH_SIZE]
        params = {"symbol": ",".join(chunk), "apikey": api_key, "format": "JSON", "interval": "1day"}
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[Explore] Twelve Data chunk error: {e}")
            continue
        all_quotes.extend(_parse_batch_quote_response(data, chunk))
    return all_quotes


def _explore_response(quotes: list, all_key: str):
    for q in quotes:
        if q.get("percent_change") is None and q.get("close") and q.get("previous_close"):
            prev = q["previous_close"] or 0
            if prev:
                q["percent_change"] = ((q["close"] - prev) / prev) * 100
        q.setdefault("percent_change", 0)
        q.setdefault("volume", 0)
    by_change = sorted(quotes, key=lambda x: (x.get("percent_change") or 0), reverse=True)
    by_volume = sorted(quotes, key=lambda x: (x.get("volume") or 0), reverse=True)
    return {
        "top_gainers": by_change[:10],
        "top_losers": by_change[-10:][::-1],
        "top_volume": by_volume[:10],
        all_key: by_change,
    }


@app.get("/explore/forex")
async def explore_forex():
    """Forex market overview: top gainers, losers, by volume (Twelve Data)."""
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        return {"error": "TWELVE_DATA_API_KEY not set", "top_gainers": [], "top_losers": [], "top_volume": [], "all_pairs": []}
    quotes = _fetch_quotes_batch(FOREX_SYMBOLS, api_key)
    return _explore_response(quotes, "all_pairs")


@app.get("/explore/crypto")
async def explore_crypto():
    """Crypto market overview: top gainers, losers, by volume (Twelve Data)."""
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        return {"error": "TWELVE_DATA_API_KEY not set", "top_gainers": [], "top_losers": [], "top_volume": [], "all_tokens": []}
    quotes = _fetch_quotes_batch(CRYPTO_SYMBOLS, api_key)
    return _explore_response(quotes, "all_tokens")


# ---------- Token detail API (MongoDB cache or CoinMarketCap) ----------


def _token_detail_from_db(symbol: str):
    """Return token detail from MongoDB if available. Symbol must be normalized."""
    from .db import token_detail_collection, normalize_symbol
    coll = token_detail_collection()
    if coll is None:
        return None
    sym = normalize_symbol(symbol)
    doc = coll.find_one({"symbol": sym})
    if not doc:
        return None
    doc.pop("_id", None)
    doc.pop("updated_at", None)
    return doc


@app.get("/token/{symbol}")
async def get_token_detail(symbol: str, convert: str = "USD"):
    """
    Fetch all live data for a single token. When MONGODB_URI is set, reads from cache; else from CoinMarketCap.
    Symbol can be: BTC, ETH, BTCUSDT, BTC-PERP, etc.
    """
    detail = _token_detail_from_db(symbol)
    if detail is not None:
        return {"success": True, "data": detail}
    from .market.cmc_client import CMCClient
    from .market.cache_refresh import upsert_token_detail

    cmc_key = os.getenv("CMC_API_KEY")
    if not cmc_key:
        raise HTTPException(status_code=500, detail="CMC_API_KEY not set (needed for token metadata)")
    try:
        client = CMCClient(api_key=cmc_key)
        detail = client.get_token_detail_with_retry(symbol, convert=convert)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Token not found: {symbol}")
    # Override price with Pyth
    from .market.pyth_client import PythClient
    pyth_price = PythClient().get_price(symbol)
    if pyth_price is not None:
        detail["price"] = pyth_price
    upsert_token_detail(detail)
    return {"success": True, "data": detail}


@app.get("/tokens")
async def get_tokens_batch(symbols: str, convert: str = "USD"):
    """
    Fetch detailed data for multiple tokens. When MONGODB_URI is set, reads from cache; else from CoinMarketCap.
    Query param: symbols = comma-separated, e.g. symbols=BTC,ETH,SOL,BNB
    """
    from .db import token_detail_collection, normalize_symbol

    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()][:50]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="symbols query param required (e.g. symbols=BTC,ETH,SOL)")

    coll = token_detail_collection()
    if coll is not None:
        norm_symbols = [normalize_symbol(s) for s in symbol_list]
        cursor = coll.find({"symbol": {"$in": norm_symbols}})
        data = []
        for doc in cursor:
            doc = dict(doc)
            doc.pop("_id", None)
            doc.pop("updated_at", None)
            data.append(doc)
        if data:
            return {"success": True, "count": len(data), "data": data}

    from .market.cmc_client import CMCClient
    from .market.cache_refresh import upsert_token_details

    cmc_key = os.getenv("CMC_API_KEY")
    if not cmc_key:
        raise HTTPException(status_code=500, detail="CMC_API_KEY not set (needed for token metadata)")
    try:
        client = CMCClient(api_key=cmc_key)
        data = client.get_tokens_batch(symbol_list, convert=convert)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    # Override prices with Pyth
    from .market.pyth_client import PythClient
    pyth_prices = PythClient().get_prices_batch(symbol_list)
    for item in data:
        sym = item.get("symbol", "")
        if sym in pyth_prices:
            item["price"] = pyth_prices[sym]
    upsert_token_details(data)
    return {"success": True, "count": len(data), "data": data}


# ---------- Token analysis (intro, scores, social sentiment; historical is separate) ----------


@app.get("/token/{symbol}/analysis")
async def get_token_analysis(
    symbol: str,
    include_intro: bool = True,
    include_social: bool = True,
):
    """
    Token analysis for detail/audit pages (no historical data; use GET /token/{symbol}/historical separately).
    Token data comes from MongoDB cache when MONGODB_URI is set, else from CoinMarketCap. Intro/social use OpenAI.
    """
    from .market.token_analysis import build_token_analysis

    from .market.cache_refresh import upsert_token_detail

    token_detail = _token_detail_from_db(symbol)
    if token_detail is None:
        from .market.cmc_client import CMCClient
        cmc_key = os.getenv("CMC_API_KEY")
        if not cmc_key:
            raise HTTPException(status_code=500, detail="CMC_API_KEY not set (needed for token metadata)")
        try:
            cmc = CMCClient(api_key=cmc_key)
            token_detail = cmc.get_token_detail_with_retry(symbol)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        if token_detail is None:
            raise HTTPException(status_code=404, detail=f"Token not found: {symbol}")
        upsert_token_detail(token_detail)
    # Override price with Pyth
    from .market.pyth_client import PythClient
    pyth_price = PythClient().get_price(symbol)
    if pyth_price is not None:
        token_detail["price"] = pyth_price

    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set (required for intro and social)")

    try:
        analysis = build_token_analysis(
            token_detail=token_detail,
            include_intro=include_intro,
            include_social=include_social,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {e}") from e

    return {"success": True, "data": analysis}


# ---------- Token historical chart data (separate; can be slow) ----------


def _historical_from_db(symbol: str, range_key: str):
    """Return historical chart data from MongoDB if available."""
    from .db import token_historical_collection, normalize_symbol
    coll = token_historical_collection()
    if coll is None:
        return None
    sym = normalize_symbol(symbol)
    range_key = (range_key or "1y").strip().lower()
    doc = coll.find_one({"symbol": sym, "range": range_key})
    if not doc:
        return None
    return {"range": doc.get("range", range_key), "data": doc.get("data", [])}


@app.get("/token/{symbol}/historical")
async def get_token_historical(
    symbol: str,
    range_key: str = Query("1y", alias="range", description="Chart range: 24h, 7d, 1m, 3m, 1y, max"),
):
    """
    Historical price/chart data for a token. When MONGODB_URI is set, reads from cache; else Twelve Data.
    Returns: { "range": "<key>", "data": [ { "date", "timestamp", "price", "open", "high", "low", "volume" }, ... ] }.
    """
    result = _historical_from_db(symbol, range_key)
    if result is not None:
        return {"success": True, "data": result}

    from .market.market import MarketData
    from .market.token_analysis import get_historical_chart_data
    from .market.cache_refresh import upsert_token_historical

    twelve_key = os.getenv("TWELVE_DATA_API_KEY")
    if not twelve_key:
        raise HTTPException(status_code=500, detail="TWELVE_DATA_API_KEY not set")

    try:
        market_data = MarketData(twelve_data_api_key=twelve_key)
        result = get_historical_chart_data(symbol, range_key, market_data)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Historical data failed: {e}") from e

    upsert_token_historical(symbol, range_key, result)
    return {"success": True, "data": result}


# ---------- Pyth prices (from MongoDB cache when MONGODB_URI is set) ----------


@app.get("/pyth/prices")
async def get_pyth_prices():
    """
    Return cached Pyth prices (BTC/USD, ETH/USD, BNB/USD). Filled by background refresh every 1 min.
    Response: { "BTC/USD": { "price": number, "conf": number, "publishTime": number }, ... }.
    """
    from .db import pyth_prices_collection
    coll = pyth_prices_collection()
    if coll is None:
        return {}
    out = {}
    for doc in coll.find({}):
        pair = doc.get("pair")
        if pair:
            out[pair] = {
                "price": doc.get("price", 0),
                "conf": doc.get("conf", 0),
                "publishTime": doc.get("publishTime", 0),
            }
    return out
