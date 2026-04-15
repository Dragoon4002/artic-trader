"""BaseExecutor ABC — interface for all trade execution backends."""
from abc import ABC, abstractmethod
from typing import Optional


class BaseExecutor(ABC):
    @abstractmethod
    async def open_long(self, symbol: str, size_usdt: float, leverage: int,
                        tp_price: Optional[float] = None, sl_price: Optional[float] = None): ...

    @abstractmethod
    async def open_short(self, symbol: str, size_usdt: float, leverage: int,
                         tp_price: Optional[float] = None, sl_price: Optional[float] = None): ...

    @abstractmethod
    async def close_position(self, symbol: str): ...

    @abstractmethod
    async def get_position(self, symbol: str): ...

    @abstractmethod
    async def get_balance(self): ...

    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int): ...

    @abstractmethod
    async def get_funding_rate(self, symbol: str): ...
