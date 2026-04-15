"""
Pydantic models for request/response schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from enum import Enum
from datetime import datetime


class PositionSide(str, Enum):
    """Position side enumeration"""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class Action(str, Enum):
    """Trading action enumeration"""
    OPEN_LONG = "OPEN_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


class StartRequest(BaseModel):
    """Request model for starting a trading session"""
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    amount_usdt: float = Field(..., gt=0, description="Position size in USDT")
    leverage: int = Field(..., ge=1, le=125, description="Leverage multiplier (1-125)")
    poll_seconds: float = Field(default=1.0, ge=0.1, description="Polling interval in seconds")
    tp_pct: Optional[float] = Field(default=None, ge=0, le=1, description="Take profit percentage (e.g., 0.05 for 5%)")
    sl_pct: Optional[float] = Field(default=None, ge=0, le=1, description="Stop loss percentage (e.g., 0.02 for 2%)")
    risk_profile: Optional[str] = Field(default="moderate", description="Risk profile for LLM planning")
    primary_timeframe: Optional[str] = Field(default="15m", description="Primary decision timeframe (1m/5m/15m/1h/4h)")
    live_mode: Optional[bool] = Field(default=False, description="If true, execute trades on Weex (real account)")
    tp_sl_mode: Optional[Literal["fixed", "dynamic"]] = Field(
        default="fixed",
        description="TP/SL mode: 'fixed' = use tp_pct/sl_pct; 'dynamic' = ATR-based SL and R:R TP, adjustable by supervisor"
    )
    supervisor_interval_seconds: Optional[float] = Field(
        default=60.0,
        ge=30,
        le=300,
        description="Seconds between LLM supervisor checks when in position (only used when > 0)"
    )
    llm_provider: Optional[str] = Field(
        default=None,
        description="LLM to use: 'openai' (GPT), 'anthropic' (Claude), or 'deepseek'. Backend normalizes and ignores invalid values."
    )
    indicators: Optional[List[str]] = Field(
        default=None,
        description="TradingView indicators to consider in AI analysis (e.g., RSI, MACD, Bollinger Bands)"
    )


class StatusResponse(BaseModel):
    """Response model for trading status"""
    running: bool
    symbol: Optional[str] = None
    last_price: Optional[float] = None
    amount_usdt: Optional[float] = None
    config_leverage: Optional[int] = None
    side: PositionSide = PositionSide.FLAT
    entry_price: Optional[float] = None
    position_size_usdt: Optional[float] = None
    leverage: Optional[int] = None
    unrealized_pnl_usdt: Optional[float] = None
    last_action: Optional[Action] = None
    last_reason: Optional[str] = None
    active_strategy: Optional[str] = None


class StrategyPlan(BaseModel):
    """LLM-generated strategy plan"""
    strategy: str = Field(..., description="Strategy name (e.g., 'momentum', 'mean_reversion')")
    lookback: int = Field(..., ge=1, description="Lookback period for indicators")
    threshold: float = Field(..., description="Signal threshold")
    max_loss_pct: float = Field(..., ge=0, le=1, description="Maximum loss percentage")


class SupervisorResponse(BaseModel):
    """Response from LLM supervisor check (cycle-based)"""
    action: Literal["KEEP", "CLOSE", "ADJUST_TP_SL"] = Field(
        ..., description="KEEP = no change, CLOSE = close position, ADJUST_TP_SL = recompute dynamic TP/SL"
    )
    reasoning: str = Field(default="", description="Short explanation")


class Candle(BaseModel):
    """OHLCV candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketRegimeSummary(BaseModel):
    """Compact market regime summary for LLM planning"""
    symbol: str
    exchange: str = "coinmarketcap"
    timestamp: datetime
    chosen_primary_timeframe: str
    bar_count_used: int
    
    # Volatility metrics
    atr: Optional[float] = None
    realized_vol_recent: Optional[float] = None  # Recent window (2 days)
    realized_vol_medium: Optional[float] = None  # Medium window (14 days)
    vol_ratio: Optional[float] = None  # recent/medium or 7d/30d
    
    # Trend/range metrics
    adx: Optional[float] = None
    ma_slope: Optional[float] = None  # Moving average slope
    range_compression_flag: bool = False
    range_expansion_flag: bool = False
    
    # Funding stats (7-30 days)
    funding_mean: Optional[float] = None
    funding_std: Optional[float] = None
    funding_p5: Optional[float] = None  # 5th percentile
    funding_p95: Optional[float] = None  # 95th percentile
    funding_current: Optional[float] = None
    
    # Open interest stats
    oi_slope_24h: Optional[float] = None
    oi_slope_48h: Optional[float] = None
    oi_zscore: Optional[float] = None  # vs medium window
    oi_spike_detected: bool = False
    
    # Liquidity/noise hints
    spread_proxy: Optional[float] = None  # (high-low)/close
    candle_wickiness: Optional[float] = None  # Average wick ratio
    churn_metric: Optional[float] = None  # Volume/price volatility ratio
    
    # Optional: last 50 candles (hard cap)
    last_50_candles: Optional[List[dict]] = None


class AIPlannerResponse(BaseModel):
    """Complete AI planner analysis response"""
    symbol: str
    primary_timeframe: str
    bar_count_used: int
    market_regime_summary: MarketRegimeSummary
    strategy_plan: StrategyPlan
    strategy_shortlist: List[str]
    analysis_paragraph: str = Field(..., description="Detailed explanation of why this strategy should be used")
    quant_algo_description: str = Field(..., description="Description of the quant algorithm that will be executed")


class Position(BaseModel):
    """Paper position model"""
    side: PositionSide = PositionSide.FLAT
    entry_price: Optional[float] = None
    size_usdt: Optional[float] = None
    leverage: Optional[int] = None
    tp_pct: Optional[float] = None
    sl_pct: Optional[float] = None
