"""
Paper trading position management
"""
from typing import Tuple, Optional
from ..schemas import PositionSide, Position


class PaperPosition:
    """
    Manages a paper trading position with PnL calculation and SL/TP checks.
    Supports fixed TP/SL (tp_pct/sl_pct) or dynamic price-based TP/SL (tp_price/sl_price).
    """
    
    def __init__(self):
        self.side = PositionSide.FLAT
        self.entry_price: Optional[float] = None
        self.size_usdt: Optional[float] = None
        self.leverage: Optional[int] = None
        self.tp_pct: Optional[float] = None
        self.sl_pct: Optional[float] = None
        self.tp_price: Optional[float] = None
        self.sl_price: Optional[float] = None
    
    def open_long(self, entry_price: float, size_usdt: float, leverage: int, 
                  tp_pct: float = None, sl_pct: float = None,
                  tp_price: float = None, sl_price: float = None):
        """Open a long position. Use either (tp_pct, sl_pct) or (tp_price, sl_price)."""
        self.side = PositionSide.LONG
        self.entry_price = entry_price
        self.size_usdt = size_usdt
        self.leverage = leverage
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.tp_price = tp_price
        self.sl_price = sl_price
    
    def open_short(self, entry_price: float, size_usdt: float, leverage: int,
                   tp_pct: float = None, sl_pct: float = None,
                   tp_price: float = None, sl_price: float = None):
        """Open a short position. Use either (tp_pct, sl_pct) or (tp_price, sl_price)."""
        self.side = PositionSide.SHORT
        self.entry_price = entry_price
        self.size_usdt = size_usdt
        self.leverage = leverage
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.tp_price = tp_price
        self.sl_price = sl_price
    
    def close(self):
        """Close the current position"""
        self.side = PositionSide.FLAT
        self.entry_price = None
        self.size_usdt = None
        self.leverage = None
        self.tp_pct = None
        self.sl_pct = None
        self.tp_price = None
        self.sl_price = None
    
    def update_dynamic_tp_sl(self, tp_price: float, sl_price: float):
        """Update dynamic TP/SL price levels (for supervisor ADJUST_TP_SL)."""
        self.tp_price = tp_price
        self.sl_price = sl_price
    
    def unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized PnL
        
        For LONG: PnL = (current_price - entry_price) / entry_price * size_usdt * leverage
        For SHORT: PnL = (entry_price - current_price) / entry_price * size_usdt * leverage
        """
        if self.side == PositionSide.FLAT or self.entry_price is None:
            return 0.0
        
        if self.side == PositionSide.LONG:
            pnl_pct = (current_price - self.entry_price) / self.entry_price
        else:  # SHORT
            pnl_pct = (self.entry_price - current_price) / self.entry_price
        
        return pnl_pct * self.size_usdt * self.leverage
    
    def check_tp_sl(self, current_price: float) -> Tuple[bool, str]:
        """
        Check if take profit or stop loss is triggered.
        Uses tp_price/sl_price if set (dynamic), else tp_pct/sl_pct (fixed).
        Returns: (triggered: bool, reason: str)
        """
        if self.side == PositionSide.FLAT:
            return False, ""
        
        # Dynamic: price-based levels
        if self.tp_price is not None and self.sl_price is not None:
            if self.side == PositionSide.LONG:
                if current_price >= self.tp_price:
                    return True, f"TP hit (price ${current_price:,.2f} >= ${self.tp_price:,.2f})"
                if current_price <= self.sl_price:
                    return True, f"SL hit (price ${current_price:,.2f} <= ${self.sl_price:,.2f})"
            else:  # SHORT
                if current_price <= self.tp_price:
                    return True, f"TP hit (price ${current_price:,.2f} <= ${self.tp_price:,.2f})"
                if current_price >= self.sl_price:
                    return True, f"SL hit (price ${current_price:,.2f} >= ${self.sl_price:,.2f})"
            return False, ""
        
        # Fixed: percentage-based
        pnl_pct = self.unrealized_pnl(current_price) / (self.size_usdt * self.leverage)
        if self.tp_pct and pnl_pct >= self.tp_pct:
            return True, f"TP hit ({pnl_pct*100:.2f}% >= {self.tp_pct*100:.2f}%)"
        if self.sl_pct and pnl_pct <= -self.sl_pct:
            return True, f"SL hit ({pnl_pct*100:.2f}% <= -{self.sl_pct*100:.2f}%)"
        return False, ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "side": self.side.value,
            "entry_price": self.entry_price,
            "size_usdt": self.size_usdt,
            "leverage": self.leverage,
            "tp_pct": self.tp_pct,
            "sl_pct": self.sl_pct,
            "tp_price": self.tp_price,
            "sl_price": self.sl_price,
        }
