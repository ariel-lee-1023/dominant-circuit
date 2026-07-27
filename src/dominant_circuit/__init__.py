"""
Dominant-Circuit zero-order decision engine.
"""

from .engine import DominantCircuitEngine
from .solvers import (
    solve_optimal_stopping,
    solve_additive_utility,
    verify_bellman_residual,
)

__all__ = [
    "DominantCircuitEngine",
    "solve_optimal_stopping",
    "solve_additive_utility",
    "verify_bellman_residual",
]
