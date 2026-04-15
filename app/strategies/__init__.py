"""
Strategy-specific signal computation.
Uses quant_algos library for algorithm implementations.
"""
from .signals import compute_strategy_signal
from . import quant_algos

__all__ = ["compute_strategy_signal", "quant_algos"]
