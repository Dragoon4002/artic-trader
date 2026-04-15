"""
Market Analysis Module
Computes features from historical data and builds MarketRegimeSummary for LLM
"""
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from ..schemas import MarketRegimeSummary, Candle


class MarketAnalyzer:
    """
    Analyzes market data and computes features for regime detection
    """
    
    # Timeframe to minutes mapping
    TIMEFRAME_MINUTES = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }
    
    @staticmethod
    def choose_timeframe_and_lookback(
        primary_timeframe: str,
        risk_profile: str = "moderate",
        strategy_hint: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Determine bar count based on timeframe, risk profile, and strategy
        
        Returns:
            (bar_count, min_bars_for_regime)
        """
        timeframe_minutes = MarketAnalyzer.TIMEFRAME_MINUTES.get(primary_timeframe, 15)
        
        # Base bar counts by timeframe
        if timeframe_minutes <= 5:  # 1m, 5m
            base_bars = 2000  # ~33 hours to 6.9 days
        elif timeframe_minutes <= 15:  # 15m
            base_bars = 2000  # ~20.8 days
        elif timeframe_minutes <= 60:  # 30m, 1h
            base_bars = 2000  # ~83 days for 1h
        else:  # 4h, 1d
            base_bars = 1000  # ~166 days for 4h
        
        # Adjust based on risk profile
        if risk_profile == "conservative":
            base_bars = int(base_bars * 1.5)  # More context
        elif risk_profile == "aggressive":
            base_bars = int(base_bars * 0.8)  # Focus on recent
        
        # Adjust based on strategy type
        if strategy_hint == "trend_following":
            base_bars = int(base_bars * 1.2)  # Need longer context
        elif strategy_hint == "mean_reversion":
            base_bars = int(base_bars * 0.9)  # Medium lookback
        
        # Minimum bars for regime detection
        min_bars = 200
        
        return base_bars, min_bars
    
    @staticmethod
    def compute_features(
        candles: List[Candle],
        funding_data: Optional[List[Dict]] = None,
        oi_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Compute all market features from candles and optional funding/OI data
        
        Args:
            candles: List of OHLCV candles (sorted by timestamp, oldest first)
            funding_data: Optional list of funding rate data points
            oi_data: Optional list of open interest data points
            
        Returns:
            Dictionary of computed features
        """
        if not candles or len(candles) < 20:
            return {}
        
        features = {}
        
        # Multi-window splits
        total_bars = len(candles)
        recent_window = min(288, total_bars)  # ~2 days for 15m, adjust for other timeframes
        medium_window = min(2016, total_bars)  # ~14 days for 15m
        long_window = min(12960, total_bars)  # ~90 days for 15m
        
        recent_candles = candles[-recent_window:]
        medium_candles = candles[-medium_window:]
        long_candles = candles[-long_window:] if total_bars >= long_window else candles
        
        # 1. Volatility metrics
        features.update(MarketAnalyzer._compute_volatility_metrics(
            recent_candles, medium_candles, long_candles
        ))
        
        # 2. Trend/range metrics
        features.update(MarketAnalyzer._compute_trend_metrics(
            recent_candles, medium_candles, long_candles
        ))
        
        # 3. Funding stats (if available)
        if funding_data:
            features.update(MarketAnalyzer._compute_funding_stats(funding_data))
        
        # 4. Open interest stats (if available)
        if oi_data:
            features.update(MarketAnalyzer._compute_oi_stats(oi_data, medium_window))
        
        # 5. Liquidity/noise metrics
        features.update(MarketAnalyzer._compute_liquidity_metrics(recent_candles))
        
        return features
    
    @staticmethod
    def _compute_volatility_metrics(
        recent: List[Candle],
        medium: List[Candle],
        long: List[Candle]
    ) -> Dict:
        """Compute ATR and realized volatility metrics"""
        metrics = {}
        
        # ATR (Average True Range) - 14 period
        if len(recent) >= 14:
            true_ranges = []
            for i in range(1, len(recent)):
                tr = max(
                    recent[i].high - recent[i].low,
                    abs(recent[i].high - recent[i-1].close),
                    abs(recent[i].low - recent[i-1].close)
                )
                true_ranges.append(tr)
            
            if true_ranges:
                metrics["atr"] = sum(true_ranges[-14:]) / min(14, len(true_ranges))
        
        # Realized volatility (annualized)
        def compute_realized_vol(candles: List[Candle]) -> Optional[float]:
            if len(candles) < 2:
                return None
            
            returns = []
            for i in range(1, len(candles)):
                ret = math.log(candles[i].close / candles[i-1].close)
                returns.append(ret)
            
            if not returns:
                return None
            
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            std_dev = math.sqrt(variance)
            
            # Annualize (assuming candles are 15m, adjust multiplier as needed)
            periods_per_year = 35040  # 15m candles per year
            annualized_vol = std_dev * math.sqrt(periods_per_year)
            
            return annualized_vol
        
        metrics["realized_vol_recent"] = compute_realized_vol(recent)
        metrics["realized_vol_medium"] = compute_realized_vol(medium)
        
        # Volatility ratio
        if metrics.get("realized_vol_recent") and metrics.get("realized_vol_medium"):
            if metrics["realized_vol_medium"] > 0:
                metrics["vol_ratio"] = metrics["realized_vol_recent"] / metrics["realized_vol_medium"]
        
        return metrics
    
    @staticmethod
    def _compute_trend_metrics(
        recent: List[Candle],
        medium: List[Candle],
        long: List[Candle]
    ) -> Dict:
        """Compute ADX, MA slope, and range compression/expansion"""
        metrics = {}
        
        # Simple ADX approximation (simplified version)
        if len(medium) >= 14:
            # Directional movement
            plus_dm = []
            minus_dm = []
            
            for i in range(1, len(medium)):
                up_move = medium[i].high - medium[i-1].high
                down_move = medium[i-1].low - medium[i].low
                
                if up_move > down_move and up_move > 0:
                    plus_dm.append(up_move)
                else:
                    plus_dm.append(0)
                
                if down_move > up_move and down_move > 0:
                    minus_dm.append(down_move)
                else:
                    minus_dm.append(0)
            
            # Smooth and compute ADX (simplified)
            if plus_dm and minus_dm:
                avg_plus = sum(plus_dm[-14:]) / 14
                avg_minus = sum(minus_dm[-14:]) / 14
                
                if avg_plus + avg_minus > 0:
                    dx = 100 * abs(avg_plus - avg_minus) / (avg_plus + avg_minus)
                    metrics["adx"] = dx
        
        # Moving average slope (20 period)
        if len(medium) >= 20:
            ma_20_old = sum(c.close for c in medium[-20:-10]) / 10
            ma_20_new = sum(c.close for c in medium[-10:]) / 10
            price_change = medium[-1].close - medium[-20].close
            
            if medium[-20].close > 0:
                metrics["ma_slope"] = price_change / medium[-20].close
        
        # Range compression/expansion
        if len(recent) >= 10 and len(medium) >= 20:
            recent_range = max(c.high for c in recent[-10:]) - min(c.low for c in recent[-10:])
            medium_range = max(c.high for c in medium[-20:]) - min(c.low for c in medium[-20:])
            
            if medium_range > 0:
                range_ratio = recent_range / medium_range
                metrics["range_compression_flag"] = range_ratio < 0.7
                metrics["range_expansion_flag"] = range_ratio > 1.3
        
        return metrics
    
    @staticmethod
    def _compute_funding_stats(funding_data: List[Dict]) -> Dict:
        """Compute funding rate statistics"""
        if not funding_data:
            return {}
        
        rates = [d.get("rate", 0) for d in funding_data if "rate" in d]
        if not rates:
            return {}
        
        metrics = {}
        metrics["funding_mean"] = sum(rates) / len(rates)
        
        # Standard deviation
        mean = metrics["funding_mean"]
        variance = sum((r - mean) ** 2 for r in rates) / len(rates)
        metrics["funding_std"] = math.sqrt(variance)
        
        # Percentiles
        sorted_rates = sorted(rates)
        metrics["funding_p5"] = sorted_rates[int(len(sorted_rates) * 0.05)]
        metrics["funding_p95"] = sorted_rates[int(len(sorted_rates) * 0.95)]
        metrics["funding_current"] = rates[-1] if rates else None
        
        return metrics
    
    @staticmethod
    def _compute_oi_stats(oi_data: List[Dict], medium_window: int) -> Dict:
        """Compute open interest statistics"""
        if not oi_data or len(oi_data) < 2:
            return {}
        
        metrics = {}
        
        # OI slope (24h and 48h)
        if len(oi_data) >= 48:
            oi_24h_old = oi_data[-48].get("value", 0)
            oi_24h_new = oi_data[-24].get("value", 0)
            if oi_24h_old > 0:
                metrics["oi_slope_24h"] = (oi_24h_new - oi_24h_old) / oi_24h_old
        
        if len(oi_data) >= 96:
            oi_48h_old = oi_data[-96].get("value", 0)
            oi_48h_new = oi_data[-48].get("value", 0)
            if oi_48h_old > 0:
                metrics["oi_slope_48h"] = (oi_48h_new - oi_48h_old) / oi_48h_old
        
        # Z-score vs medium window
        if len(oi_data) >= medium_window:
            medium_oi = [d.get("value", 0) for d in oi_data[-medium_window:]]
            if medium_oi:
                mean_oi = sum(medium_oi) / len(medium_oi)
                variance = sum((o - mean_oi) ** 2 for o in medium_oi) / len(medium_oi)
                std_oi = math.sqrt(variance) if variance > 0 else 1
                
                current_oi = oi_data[-1].get("value", 0)
                if std_oi > 0:
                    metrics["oi_zscore"] = (current_oi - mean_oi) / std_oi
                    metrics["oi_spike_detected"] = abs(metrics["oi_zscore"]) > 2.0
        
        return metrics
    
    @staticmethod
    def _compute_liquidity_metrics(candles: List[Candle]) -> Dict:
        """Compute spread proxy, wickiness, and churn"""
        if not candles:
            return {}
        
        metrics = {}
        
        # Spread proxy: average (high-low)/close
        spreads = [(c.high - c.low) / c.close for c in candles if c.close > 0]
        if spreads:
            metrics["spread_proxy"] = sum(spreads) / len(spreads)
        
        # Candle wickiness: average wick ratio
        wick_ratios = []
        for c in candles:
            body = abs(c.close - c.open)
            upper_wick = c.high - max(c.open, c.close)
            lower_wick = min(c.open, c.close) - c.low
            total_range = c.high - c.low
            
            if total_range > 0:
                wick_ratio = (upper_wick + lower_wick) / total_range
                wick_ratios.append(wick_ratio)
        
        if wick_ratios:
            metrics["candle_wickiness"] = sum(wick_ratios) / len(wick_ratios)
        
        # Churn metric: volume / price volatility
        if len(candles) >= 2:
            volumes = [c.volume for c in candles]
            prices = [c.close for c in candles]
            
            price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] 
                           for i in range(1, len(prices)) if prices[i-1] > 0]
            
            if price_changes and volumes:
                avg_vol = sum(volumes) / len(volumes)
                avg_price_vol = sum(price_changes) / len(price_changes)
                
                if avg_price_vol > 0:
                    metrics["churn_metric"] = avg_vol / avg_price_vol
        
        return metrics
    
    @staticmethod
    def build_summary(
        symbol: str,
        primary_timeframe: str,
        bar_count: int,
        features: Dict,
        last_50_candles: Optional[List[Candle]] = None
    ) -> MarketRegimeSummary:
        """
        Build MarketRegimeSummary from computed features
        
        Args:
            symbol: Trading symbol
            primary_timeframe: Primary timeframe used
            bar_count: Number of bars used
            features: Computed features dictionary
            last_50_candles: Optional last 50 candles (hard cap)
        """
        # Convert last 50 candles to dict format
        candles_dict = None
        if last_50_candles:
            candles_dict = [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume
                }
                for c in last_50_candles[-50:]  # Hard cap at 50
            ]
        
        return MarketRegimeSummary(
            symbol=symbol,
            exchange="coinmarketcap",
            timestamp=datetime.now(),
            chosen_primary_timeframe=primary_timeframe,
            bar_count_used=bar_count,
            atr=features.get("atr"),
            realized_vol_recent=features.get("realized_vol_recent"),
            realized_vol_medium=features.get("realized_vol_medium"),
            vol_ratio=features.get("vol_ratio"),
            adx=features.get("adx"),
            ma_slope=features.get("ma_slope"),
            range_compression_flag=features.get("range_compression_flag", False),
            range_expansion_flag=features.get("range_expansion_flag", False),
            funding_mean=features.get("funding_mean"),
            funding_std=features.get("funding_std"),
            funding_p5=features.get("funding_p5"),
            funding_p95=features.get("funding_p95"),
            funding_current=features.get("funding_current"),
            oi_slope_24h=features.get("oi_slope_24h"),
            oi_slope_48h=features.get("oi_slope_48h"),
            oi_zscore=features.get("oi_zscore"),
            oi_spike_detected=features.get("oi_spike_detected", False),
            spread_proxy=features.get("spread_proxy"),
            candle_wickiness=features.get("candle_wickiness"),
            churn_metric=features.get("churn_metric"),
            last_50_candles=candles_dict
        )
    
    @staticmethod
    def suggest_strategy_shortlist(summary: MarketRegimeSummary) -> List[str]:
        """
        Suggest strategy shortlist based on market regime summary.
        Includes quant algo strategies: momentum, trend_following, mean_reversion,
        breakout, donchian_channel, ma_crossover, ema_crossover, macd_signal,
        supertrend, rsi_signal, bollinger_reversion, z_score, etc.
        
        Returns:
            List of strategy names to consider
        """
        strategies = []
        vol_moderate = summary.realized_vol_recent and summary.realized_vol_medium
        vol_ok = False
        if vol_moderate:
            vol_ok = 0.1 < (summary.realized_vol_recent or 0) < 0.5  # Reasonable volatility
        
        trend_strength = summary.adx or 0
        range_high = summary.range_compression_flag or (summary.adx and summary.adx < 20)
        range_expanding = summary.range_expansion_flag
        
        # Trend following + quant algos (when trending)
        if trend_strength > 25 and vol_moderate and vol_ok:
            strategies.extend(["trend_following", "ma_crossover", "ema_crossover"])
            if trend_strength > 30:
                strategies.extend(["breakout", "donchian_channel", "macd_signal", "supertrend"])
        
        # Mean reversion + quant algos (when ranging)
        if range_high:
            strategies.extend(["mean_reversion", "z_score", "bollinger_reversion", "rsi_signal"])
            if range_expanding:
                strategies.extend(["bollinger_squeeze", "linear_regression_channel"])
        
        # Volatility breakout
        if range_expanding and not range_high:
            strategies.extend(["atr_breakout", "breakout"])
        
        # Funding/OI filter conditions
        funding_extreme = False
        if summary.funding_current and summary.funding_p5 and summary.funding_p95:
            funding_extreme = (summary.funding_current < summary.funding_p5 or
                             summary.funding_current > summary.funding_p95)
        if funding_extreme or summary.oi_spike_detected:
            strategies.append("funding_oi_filter")
        
        # Core strategies always available
        if "momentum" not in strategies:
            strategies.append("momentum")
        
        # Deduplicate preserving order
        seen = set()
        unique = []
        for s in strategies:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        
        return unique
