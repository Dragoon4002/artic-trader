"""
Trading Engine - Core trading loop and decision logic
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded before reading API keys (handles uvicorn --reload subprocess CWD)
_load_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_load_env, override=True)
import time
from typing import Optional, Deque, Tuple, List
from collections import deque
from .schemas import Action, PositionSide, Candle
from .market.market import MarketData, _normalize_symbol
from .executor.paper import PaperPosition
from .llm.llm_planner import LLMPlanner
from .log_buffer import emit as log_emit
from .strategies import compute_strategy_signal
from .onchain_logger import OnchainLogger
from .onchain_trade_logger import OnchainTradeLogger
from .executor.pancake_executor_stub import PancakeExecutorStub, compute_amount as pancake_compute_amount
from .market.price_listener import PriceListener
from . import hub_callback


class TradingEngine:
    """
    Main trading engine that runs the per-second trading loop
    """
    
    def __init__(self):
        self.running = False
        self.symbol: Optional[str] = None
        self.last_price: Optional[float] = None
        self.position = PaperPosition()
        self.last_action: Optional[Action] = None
        self.last_reason: Optional[str] = None
        
        # Trading parameters
        self.amount_usdt: Optional[float] = None
        self.leverage: Optional[int] = None
        self.poll_seconds: float = 1.0
        self.tp_pct: Optional[float] = None
        self.sl_pct: Optional[float] = None
        
        # Strategy plan from LLM
        self.strategy_plan = None
        
        # Full AI planner response (for AI log upload)
        self.ai_planner_response = None
        
        # Primary timeframe (for candle-based strategies)
        self.primary_timeframe: str = "15m"
        
        # Price history for signal calculation
        self.price_history: Deque[float] = deque(maxlen=200)
        
        # Candle cache for trend_following, mean_reversion (refreshed periodically)
        self._candle_cache: Optional[List[Candle]] = None
        self._last_candle_refresh_tick: int = 0

        # Live trading - use Pancake Perps stub (real execution not yet implemented)
        self._live_mode: bool = False
        self._trading_client: Optional[PancakeExecutorStub] = None
        self._executor: Optional[object] = None  # BaseExecutor for HashKey

        # Initialize market data client (Pyth for prices, Twelve Data for candles)
        twelve_data_api_key = os.getenv("TWELVE_DATA_API_KEY", "")
        if not twelve_data_api_key:
            print("[WARN] TWELVE_DATA_API_KEY not set — candle data unavailable until key is provided.")
        self.market_data = MarketData(twelve_data_api_key=twelve_data_api_key)
        
        # LLM planner
        self.llm_planner = LLMPlanner()
        
        # Task handle for the trading loop
        self._loop_task: Optional[asyncio.Task] = None

        # Hub callback + price listener state
        self._agent_id: str = os.getenv("HUB_AGENT_ID", "")
        self._price_listener: Optional[PriceListener] = None
        self._hub_log_buffer: list = []
        
        # Supervisor + dynamic TP/SL (new architecture)
        self._tp_sl_mode: str = "fixed"  # "fixed" | "dynamic"
        self._supervisor_interval_seconds: float = 60.0
        self._last_supervisor_time: float = 0.0
        self._llm_provider_override: Optional[str] = None  # "openai" | "anthropic" | "deepseek" from start request

        # On-chain logging
        self._onchain = OnchainLogger()
        self._trade_logger = OnchainTradeLogger()
    
    def is_alive(self) -> bool:
        """Check if engine is running"""
        return self.running
    
    async def start(self, symbol: str, amount_usdt: float, leverage: int,
                   poll_seconds: float = 1.0, tp_pct: Optional[float] = None,
                   sl_pct: Optional[float] = None, risk_profile: str = "moderate",
                   primary_timeframe: str = "15m", live_mode: bool = False,
                   tp_sl_mode: str = "fixed", supervisor_interval_seconds: float = 60.0,
                   llm_provider: Optional[str] = None,
                   indicators: Optional[List[str]] = None):
        """
        Start the trading engine.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT', 'BINANCE:ETHUSDT')
            amount_usdt: Position size in USDT
            leverage: Leverage multiplier
            poll_seconds: Polling interval in seconds
            tp_pct: Take profit percentage (optional; used when tp_sl_mode=fixed)
            sl_pct: Stop loss percentage (optional; used when tp_sl_mode=fixed)
            risk_profile: Risk profile for LLM planning
            primary_timeframe: Primary decision timeframe (1m/5m/15m/1h/4h)
            live_mode: If True, use Pancake Perps stub (real execution not yet implemented)
            tp_sl_mode: 'fixed' = use tp_pct/sl_pct; 'dynamic' = ATR-based SL and R:R TP, adjustable by supervisor
            supervisor_interval_seconds: Seconds between LLM supervisor checks when in position
            llm_provider: Optional 'openai', 'anthropic', or 'deepseek' to force LLM for this session
        """
        if self.running:
            log_emit("warn", "[WARN] Engine already running. Stop it first.")
            return

        self._live_mode = live_mode
        if live_mode:
            hashkey_key = os.getenv("HASHKEY_API_KEY")
            if hashkey_key:
                from .executor.hashkey import HashKeyExecutor
                self._executor = HashKeyExecutor()
                log_emit("init", "[INIT] Live mode: HashKey Global executor")
            else:
                self._trading_client = PancakeExecutorStub()
                log_emit("init", "[INIT] Live mode: Pancake Perps stub (no HashKey key)")

        self.symbol = _normalize_symbol(symbol).upper()
        self.amount_usdt = amount_usdt
        self.leverage = leverage
        self.poll_seconds = poll_seconds
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.primary_timeframe = primary_timeframe or "15m"
        self._tp_sl_mode = (tp_sl_mode or "fixed").lower()
        self._supervisor_interval_seconds = max(30.0, float(supervisor_interval_seconds or 60.0))
        self._last_supervisor_time = 0.0
        self._llm_provider_override = (llm_provider or "").strip().lower() or None
        if self._llm_provider_override and self._llm_provider_override not in ("openai", "anthropic", "deepseek", "gemini"):
            self._llm_provider_override = None
        
        # Step 1: Get initial market context
        log_emit("init", f"\n[INIT] Starting trading session for {self.symbol}")
        log_emit("init", f"[INIT] Position size: {amount_usdt} USDT, Leverage: {leverage}x")

        initial_price = await asyncio.to_thread(self.market_data.get_price_with_retry, self.symbol)
        if initial_price is None:
            log_emit("error", f"[ERROR] Failed to fetch initial price for {self.symbol}")
            return

        self.last_price = initial_price
        self.price_history.append(initial_price)

        log_emit("init", f"[INIT] Initial price: ${initial_price:,.2f}")

        # Get market summary for context
        market_summary = await asyncio.to_thread(self.market_data.get_market_summary, self.symbol)
        if market_summary:
            pct = market_summary.get("percent_change_24h")
            vol = market_summary.get("volume_24h")
            if pct is not None:
                log_emit("init", f"[INIT] 24h Change: {pct:+.2f}%")
            if vol is not None:
                log_emit("init", f"[INIT] 24h Volume: ${vol:,.0f}")

        # Step 2: LLM Planning (called once at start) - Get full analysis for AI log upload
        log_emit("llm", f"[LLM] Planning strategy with risk profile: {risk_profile}")
        if indicators and len(indicators) > 0:
            log_emit("llm", f"[LLM] User-selected indicators: {', '.join(indicators)}")
        market_context = {
            "current_price": initial_price,
            "symbol": self.symbol,
            "market_summary": market_summary
        }

        # Get full analysis in thread pool (sync LLM HTTP calls block event loop otherwise)
        try:
            summary, strategy_plan, strategy_shortlist, analysis_paragraph, quant_algo_description = await asyncio.to_thread(
                self.llm_planner.get_full_analysis,
                symbol=self.symbol,
                amount_usdt=amount_usdt,
                leverage=leverage,
                risk_profile=risk_profile,
                primary_timeframe=primary_timeframe,
                market_context=market_context,
                llm_provider=self._llm_provider_override,
                indicators=indicators,
            )
        except Exception as e:
            log_emit("warn", f"[WARN] LLM planning failed: {e}; using default strategy")
            strategy_plan = self.llm_planner._get_default_strategy(risk_profile)
            summary = None
            strategy_shortlist = [strategy_plan.strategy]
            analysis_paragraph = "LLM planning failed; using default momentum strategy."
            quant_algo_description = f"Default: lookback {strategy_plan.lookback}, threshold {strategy_plan.threshold}"

        self.strategy_plan = strategy_plan
        # Store full response for AI log upload
        self.ai_planner_response = {
            "analysis_paragraph": analysis_paragraph,
            "quant_algo_description": quant_algo_description,
            "strategy_shortlist": strategy_shortlist,
            "market_regime_summary": summary
        }

        log_emit("llm", f"[LLM] Strategy: {self.strategy_plan.strategy}")
        log_emit("llm", f"[LLM] Lookback: {self.strategy_plan.lookback}, Threshold: {self.strategy_plan.threshold}")
        log_emit("llm", f"[LLM] Max loss: {self.strategy_plan.max_loss_pct*100:.2f}%")

        # Use strategy max_loss_pct for SL when user did not specify sl_pct
        if self.sl_pct is None:
            self.sl_pct = self.strategy_plan.max_loss_pct
            log_emit("llm", f"[LLM] Using strategy SL: {self.sl_pct*100:.2f}%")

        # Pre-fetch candles for trend_following / mean_reversion (and ATR for dynamic TP/SL)
        await asyncio.to_thread(self._refresh_candles)

        log_emit("init", f"[INIT] TP/SL mode: {self._tp_sl_mode} | Supervisor check every {self._supervisor_interval_seconds}s")
        
        # Start price listener (hub WS) if HUB_URL is set
        hub_url = os.getenv("HUB_URL", "")
        if hub_url:
            self._price_listener = PriceListener(
                hub_url=hub_url,
                symbol=self.symbol,
                internal_secret=os.getenv("INTERNAL_SECRET", ""),
            )
            await self._price_listener.start()
            log_emit("init", f"[INIT] Price listener started (hub WS)")

        # Step 3: Start trading loop
        self.running = True
        self._loop_task = asyncio.create_task(self._trading_loop())
        log_emit("start", f"[START] Trading loop started (polling every {poll_seconds}s)\n")
    
    async def stop(self, close_position: bool = True):
        """
        Stop the trading engine
        
        Args:
            close_position: Whether to close the current position
        """
        if not self.running:
            return
        
        log_emit("stop", f"\n[STOP] Stopping engine...")
        self.running = False
        
        if self._loop_task:
            await self._loop_task

        if close_position and self.position.side != PositionSide.FLAT:
            final_price = self.market_data.get_price(self.symbol)
            if final_price:
                pnl = self.position.unrealized_pnl(final_price)
                log_emit("stop", f"[STOP] Closing position at ${final_price:,.2f}")
                log_emit("stop", f"[STOP] Final PnL: {pnl:+.2f} USDT")
            if self._live_mode and self._trading_client:
                try:
                    self._trading_client.close_position(self.symbol)
                    log_emit("stop", "[STOP] Position close requested (Pancake stub)")
                except Exception as e:
                    log_emit("error", f"[ERROR] Live close failed: {e}")
            self.position.close()

        if self._price_listener:
            await self._price_listener.stop()
            self._price_listener = None

        log_emit("stop", f"[STOP] Engine stopped\n")
    
    async def _trading_loop(self):
        """
        Main trading loop - runs every poll_seconds
        """
        tick_count = 0
        
        while self.running:
            try:
                tick_count += 1
                
                # Fetch current price (hub WS → direct Pyth fallback)
                current_price = await self._get_current_price()
                
                if current_price is None:
                    log_emit("error", f"[ERROR] Price fetch failed for {self.symbol}")
                    await asyncio.sleep(self.poll_seconds)
                    continue
                
                self.last_price = current_price
                self.price_history.append(current_price)
                
                # Check SL/TP first (before making new decisions)
                if self.position.side != PositionSide.FLAT:
                    triggered, reason = self.position.check_tp_sl(current_price)
                    if triggered:
                        log_emit("sl_tp", f"[SL/TP] {reason}")
                        self._execute_action(Action.CLOSE, current_price, reason)
                        await asyncio.sleep(self.poll_seconds)
                        continue
                    # Supervisor check on cycle (LLM: KEEP / CLOSE / ADJUST_TP_SL)
                    now = time.monotonic()
                    if (self._last_supervisor_time == 0) or (now - self._last_supervisor_time >= self._supervisor_interval_seconds):
                        self._last_supervisor_time = now
                        await self._run_supervisor_check(current_price)
                        # If supervisor closed position, skip signal this tick
                        if self.position.side == PositionSide.FLAT:
                            await asyncio.sleep(self.poll_seconds)
                            continue
                
                # Refresh candles periodically for candle-based strategies
                if tick_count - self._last_candle_refresh_tick >= 300:
                    self._refresh_candles()
                    self._last_candle_refresh_tick = tick_count
                
                # Compute signal using selected strategy
                signal, signal_detail = self._compute_signal()
                
                # Decide action
                action, reason = self._decide_action(signal, signal_detail)
                
                # Execute action
                if action != Action.HOLD:
                    self._execute_action(action, current_price, reason)
                
                # Print tick log
                self._print_tick_log(current_price, action, reason)

                # Hub callbacks (if HUB_URL set)
                if self._agent_id:
                    await hub_callback.report_status(self._agent_id, self._build_status_dict(current_price))
                    if tick_count % 10 == 0:
                        await hub_callback.flush_logs(self._agent_id)

                # Wait for next poll
                await asyncio.sleep(self.poll_seconds)
            
            except Exception as e:
                log_emit("error", f"[ERROR] Trading loop error: {e}")
                await asyncio.sleep(self.poll_seconds)
    
    async def _get_current_price(self) -> Optional[float]:
        """Try hub WS price first, fall back to direct Pyth."""
        if self._price_listener:
            ws_price = self._price_listener.get_price(self.symbol)
            if ws_price is not None:
                return ws_price
        return self.market_data.get_price_with_retry(self.symbol)

    def _refresh_candles(self) -> None:
        """Refresh candle cache for candle-based strategies."""
        try:
            bar_count = max(100, self.strategy_plan.lookback * 2) if self.strategy_plan else 100
            candles = self.market_data.get_ohlcv_candles(
                symbol=self.symbol,
                timeframe=self.primary_timeframe,
                bar_count=bar_count
            )
            if candles and len(candles) > 0:
                self._candle_cache = candles
        except Exception:
            pass
    
    @staticmethod
    def _compute_atr(candles: List[Candle], period: int = 14) -> Optional[float]:
        """Compute ATR from candles. Returns None if insufficient data."""
        if not candles or len(candles) < period + 1:
            return None
        tr_list = []
        for i in range(1, len(candles)):
            high, low = candles[i].high, candles[i].low
            prev_close = candles[i - 1].close
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        if len(tr_list) < period:
            return None
        atr = sum(tr_list[-period:]) / period
        return atr
    
    def _compute_dynamic_tp_sl(self, entry_price: float, side: str, atr_mult: float = 2.0, rr_ratio: float = 2.0) -> Tuple[float, float]:
        """Compute TP and SL prices from ATR (dynamic mode). Returns (tp_price, sl_price)."""
        atr = self._compute_atr(self._candle_cache or [], 14)
        if atr is None or atr <= 0:
            # Fallback: 3% SL
            sl_dist = entry_price * 0.03
        else:
            sl_dist = atr * atr_mult
        is_long = str(side).lower() in ("long", PositionSide.LONG.value.lower())
        if is_long:
            sl_price = entry_price - sl_dist
            tp_price = entry_price + sl_dist * rr_ratio
        else:
            sl_price = entry_price + sl_dist
            tp_price = entry_price - sl_dist * rr_ratio
        return (tp_price, sl_price)

    async def _run_supervisor_check(self, current_price: float) -> None:
        """Run LLM supervisor check: KEEP, CLOSE, or ADJUST_TP_SL (dynamic only)."""
        if self.position.side == PositionSide.FLAT or not self.strategy_plan:
            return
        u_pnl = self.position.unrealized_pnl(current_price)
        notional = self.position.size_usdt * self.position.leverage
        u_pnl_pct = (u_pnl / notional) if notional else 0.0
        market_summary = self.market_data.get_market_summary(self.symbol) if self.symbol else None
        resp = self.llm_planner.supervisor_check(
            symbol=self.symbol,
            current_price=current_price,
            entry_price=self.position.entry_price,
            side=self.position.side.value.lower(),
            unrealized_pnl_usdt=u_pnl,
            unrealized_pnl_pct=u_pnl_pct,
            strategy_name=self.strategy_plan.strategy,
            tp_sl_mode=self._tp_sl_mode,
            market_summary=market_summary,
            llm_provider=self._llm_provider_override,
        )
        log_emit("supervisor", f"[SUPERVISOR] {resp.action}: {resp.reasoning}")

        # Log decision on-chain
        if self._onchain._enabled:
            u_pnl_bps = int(u_pnl_pct * 10000)  # convert to basis points
            tx_hash = await self._onchain.log_decision(
                agent_id=self._agent_id,
                symbol=self.symbol,
                action=resp.action,
                strategy=self.strategy_plan.strategy,
                confidence=75,  # TODO: extract from LLM response
                pnl_bps=u_pnl_bps,
                reasoning=resp.reasoning,
            )
            if tx_hash:
                log_emit("supervisor", f"[ON-CHAIN] Decision logged: {tx_hash}")
                # Push to hub for DB persistence
                if self._agent_id:
                    await hub_callback.report_onchain_decision(
                        self._agent_id, tx_hash, resp.reasoning,
                    )

        if resp.action == "CLOSE":
            self._execute_action(Action.CLOSE, current_price, f"supervisor: {resp.reasoning}")
        elif resp.action == "ADJUST_TP_SL" and self._tp_sl_mode == "dynamic":
            tp_price, sl_price = self._compute_dynamic_tp_sl(
                self.position.entry_price,
                self.position.side
            )
            self.position.update_dynamic_tp_sl(tp_price, sl_price)
            log_emit("supervisor", f"[SUPERVISOR] Adjusted TP=${tp_price:,.2f} SL=${sl_price:,.2f}")
    
    def _compute_signal(self) -> Tuple[float, str]:
        """
        Compute trading signal using the strategy selected by the LLM.
        
        Returns:
            (signal, detail): signal positive=bullish, negative=bearish; detail for logging.
        """
        return compute_strategy_signal(
            strategy=self.strategy_plan.strategy,
            plan=self.strategy_plan,
            price_history=self.price_history,
            candles=self._candle_cache,
        )
    
    def _decide_action(self, signal: float, signal_detail: str) -> Tuple[Action, str]:
        """
        Decide trading action based on signal and current position.
        
        Returns:
            (action, reason)
        """
        threshold = self.strategy_plan.threshold
        strat = (self.strategy_plan.strategy or "momentum").lower()
        
        # If we have a position, check if we should close it
        if self.position.side != PositionSide.FLAT:
            if self.position.side == PositionSide.LONG and signal < -threshold:
                return Action.CLOSE, f"signal reversed ({signal_detail})"
            elif self.position.side == PositionSide.SHORT and signal > threshold:
                return Action.CLOSE, f"signal reversed ({signal_detail})"
            else:
                return Action.HOLD, f"holding {self.position.side.value.lower()} ({signal_detail})"
        
        # No position - decide whether to open one
        if signal > threshold:
            reason = f"{strat} long ({signal_detail})"
            return Action.OPEN_LONG, reason
        elif signal < -threshold:
            reason = f"{strat} short ({signal_detail})"
            return Action.OPEN_SHORT, reason
        else:
            return Action.HOLD, f"signal weak ({signal_detail})"
    
    def _execute_action(self, action: Action, price: float, reason: str):
        """
        Execute a trading action (paper + optional live via Pancake stub)
        """
        self.last_action = action
        self.last_reason = reason

        if action == Action.OPEN_LONG:
            tp_pct, sl_pct, tp_price, sl_price = self.tp_pct, self.sl_pct, None, None
            if self._tp_sl_mode == "dynamic":
                tp_price, sl_price = self._compute_dynamic_tp_sl(price, PositionSide.LONG)
                log_emit("action", f"[ACTION] Dynamic TP=${tp_price:,.2f} SL=${sl_price:,.2f}")
            self.position.open_long(
                entry_price=price,
                size_usdt=self.amount_usdt,
                leverage=self.leverage,
                tp_pct=tp_pct,
                sl_pct=sl_pct,
                tp_price=tp_price,
                sl_price=sl_price
            )
            log_emit("action", f"[ACTION] OPEN_LONG at ${price:,.2f} - {reason}")

            if self._agent_id:
                asyncio.ensure_future(hub_callback.report_trade({
                    "agent_id": self._agent_id, "side": "long", "entry_price": price,
                    "size_usdt": self.amount_usdt, "leverage": self.leverage,
                    "strategy": self.strategy_plan.strategy if self.strategy_plan else None,
                }))

            asyncio.ensure_future(self._log_trade_onchain(
                "OPEN_LONG", price, 0.0, 0, reason,
            ))

            if self._live_mode and self._trading_client:
                self._execute_live_order("long", price, reason)

        elif action == Action.OPEN_SHORT:
            tp_pct, sl_pct, tp_price, sl_price = self.tp_pct, self.sl_pct, None, None
            if self._tp_sl_mode == "dynamic":
                tp_price, sl_price = self._compute_dynamic_tp_sl(price, PositionSide.SHORT)
                log_emit("action", f"[ACTION] Dynamic TP=${tp_price:,.2f} SL=${sl_price:,.2f}")
            self.position.open_short(
                entry_price=price,
                size_usdt=self.amount_usdt,
                leverage=self.leverage,
                tp_pct=tp_pct,
                sl_pct=sl_pct,
                tp_price=tp_price,
                sl_price=sl_price
            )
            log_emit("action", f"[ACTION] OPEN_SHORT at ${price:,.2f} - {reason}")

            if self._agent_id:
                asyncio.ensure_future(hub_callback.report_trade({
                    "agent_id": self._agent_id, "side": "short", "entry_price": price,
                    "size_usdt": self.amount_usdt, "leverage": self.leverage,
                    "strategy": self.strategy_plan.strategy if self.strategy_plan else None,
                }))

            asyncio.ensure_future(self._log_trade_onchain(
                "OPEN_SHORT", price, 0.0, 0, reason,
            ))

            if self._live_mode and self._trading_client:
                self._execute_live_order("short", price, reason)

        elif action == Action.CLOSE:
            if self.position.side != PositionSide.FLAT:
                pnl = self.position.unrealized_pnl(price)
                entry = self.position.entry_price
                close_side = f"CLOSE_{self.position.side.value}"
                notional = (self.position.size_usdt or 0) * (self.position.leverage or 1)
                pnl_bps = int((pnl / notional) * 10000) if notional else 0
                log_emit("action", f"[ACTION] CLOSE {self.position.side.value} at ${price:,.2f} - {reason}")
                log_emit("action", f"[ACTION] Realized PnL: {pnl:+.2f} USDT")

                if self._agent_id:
                    asyncio.ensure_future(hub_callback.report_trade({
                        "agent_id": self._agent_id, "side": self.position.side.value.lower(),
                        "entry_price": entry, "exit_price": price, "pnl": pnl,
                        "size_usdt": self.position.size_usdt, "leverage": self.position.leverage,
                        "strategy": self.strategy_plan.strategy if self.strategy_plan else None,
                        "close_reason": reason,
                    }))

                asyncio.ensure_future(self._log_trade_onchain(
                    close_side, entry, price, pnl_bps, reason,
                ))

                if self._live_mode and self._trading_client:
                    try:
                        self._trading_client.close_position(self.symbol)
                        log_emit("action", "[LIVE] Position close requested (Pancake stub)")
                    except Exception as e:
                        log_emit("error", f"[ERROR] Live close failed: {e}")

                self.position.close()
    
    def _execute_live_order(self, side: str, price: float, reason: str):
        """Execute order via Pancake Perps stub (real execution not yet implemented)."""
        if not self._trading_client:
            return
        try:
            amount = pancake_compute_amount(self.amount_usdt, self.leverage, price)
            if amount <= 0:
                log_emit("error", "[ERROR] Invalid order amount (too small)")
                return

            log_emit("action", f"[LIVE] Stub: would place {side.upper()} order: amount={amount} @ ${price:,.2f}")

            stop_loss = None
            take_profit = None
            if self._tp_sl_mode == "dynamic" and self.position.tp_price is not None and self.position.sl_price is not None:
                take_profit = self.position.tp_price
                stop_loss = self.position.sl_price
            elif self.tp_pct and self.sl_pct:
                entry = price
                is_long = side == "long"
                take_profit = entry * (1 + (self.tp_pct if is_long else -self.tp_pct))
                stop_loss = entry * (1 - (self.sl_pct if is_long else -self.sl_pct))

            # Place order (stub)
            order_response = self._trading_client.place_order(
                symbol=self.symbol,
                side=side,
                amount=amount,
                leverage=self.leverage,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
            log_emit("action", "[LIVE] Stub order 'placed' (no real execution)")

            # Stub: brief delay then fetch positions (returns empty)
            import time
            time.sleep(1)
            positions_response = self._trading_client.get_positions(symbol=self.symbol)
            
            order_id = None
            if positions_response.get("success") and positions_response.get("order"):
                main_order = positions_response["order"].get("main_order", {}) if isinstance(positions_response.get("order"), dict) else {}
                order_id = main_order.get("order_id")
                if order_id:
                    log_emit("action", f"[LIVE] Retrieved order_id: {order_id}")
            
            # Upload AI log if order_id was retrieved (stub does nothing)
            if order_id:
                self._upload_ai_log_for_order(order_id, side, price, reason, stop_loss, take_profit)
            else:
                log_emit("warn", "[WARN] Could not retrieve order_id, skipping AI log upload")

        except Exception as e:
            log_emit("error", f"[ERROR] Live order failed: {e}")

    def _upload_ai_log_for_order(self, order_id: str, side: str, price: float, reason: str, 
                                  stop_loss: Optional[float], take_profit: Optional[float]):
        """Upload AI decision log for the placed order (stub)."""
        if not self._trading_client or not self.strategy_plan:
            return

        try:
            self._trading_client.upload_ai_log(
                order_id=order_id,
                stage="Decision Making",
                model="GPT-4",
                input_data={"prompt": f"Analyze {self.symbol} market conditions and justify strategy."},
                output_data={"response": f"{self.strategy_plan.strategy} strategy selected for {self.symbol}"},
                explanation=reason,
            )
        except Exception as e:
            log_emit("error", f"[ERROR] Failed to upload AI log: {e}")

    async def _log_trade_onchain(
        self, side: str, entry_price: float, exit_price: float, pnl_bps: int, reason: str,
    ) -> None:
        """Log trade on-chain + push to hub. Gracefully skips if disabled."""
        import json as _json
        if not self._trade_logger._enabled:
            return
        try:
            detail = _json.dumps({
                "size_usdt": self.amount_usdt,
                "leverage": self.leverage,
                "strategy": self.strategy_plan.strategy if self.strategy_plan else None,
                "reason": reason,
            })
            tx_hash = await self._trade_logger.log_trade(
                agent_id=self._agent_id,
                symbol=self.symbol,
                side=side,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl_bps=pnl_bps,
                detail_json=detail,
            )
            if tx_hash:
                log_emit("action", f"[ON-CHAIN] Trade logged: {tx_hash}")
                if self._agent_id:
                    await hub_callback.report_onchain_trade(
                        self._agent_id, tx_hash, side,
                        entry_price, exit_price, pnl_bps, detail,
                    )
        except Exception as e:
            log_emit("error", f"[ERROR] On-chain trade log failed: {e}")

    def _build_status_dict(self, current_price: float) -> dict:
        """Build status dict for hub push."""
        u_pnl = None
        if self.position.side != PositionSide.FLAT and current_price:
            u_pnl = self.position.unrealized_pnl(current_price)
        return {
            "running": self.running,
            "symbol": self.symbol,
            "last_price": current_price,
            "side": self.position.side.value,
            "entry_price": self.position.entry_price,
            "position_size_usdt": self.position.size_usdt,
            "leverage": self.position.leverage,
            "unrealized_pnl_usdt": u_pnl,
            "last_action": self.last_action.value if self.last_action else None,
            "last_reason": self.last_reason,
            "active_strategy": self.strategy_plan.strategy if self.strategy_plan else None,
        }

    def _print_tick_log(self, price: float, action: Action, reason: str):
        """
        Print formatted tick log to terminal
        """
        if self.position.side == PositionSide.FLAT:
            pos_str = "FLAT"
        else:
            pos_str = f"{self.position.side.value}@{self.position.entry_price:,.2f}"
        
        if self.position.side != PositionSide.FLAT:
            u_pnl = self.position.unrealized_pnl(price)
            pnl_str = f"{u_pnl:+.2f} USDT"
        else:
            pnl_str = "0.00 USDT"
        
        log_emit("tick", f"[TICK] {self.symbol} price=${price:,.2f}")
        log_emit("tick", f"       pos={pos_str}")
        log_emit("tick", f"       uPnL={pnl_str}")
        log_emit("tick", f"       action={action.value}")
        log_emit("tick", f"       reason={reason}")
