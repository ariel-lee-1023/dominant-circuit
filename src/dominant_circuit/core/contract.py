"""Input Contract — every field defaults to None so 'not elicited' ≠ 'elicited as false/zero'."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Sequence


class Job(str, Enum):
    STOPPING = "stopping"
    MULTIOBJECTIVE = "multiobjective"
    SEQUENTIAL = "sequential"


class Horizon(str, Enum):
    FIXED_KNOWN = "fixed_known"
    FIXED_UNKNOWN_UNIFORM = "fixed_unknown_uniform"
    OPEN_ENDED_STOCHASTIC = "open_ended_stochastic"
    UNBOUNDED_STREAM = "unbounded_stream"
    FINITE_SUM = "finite_sum"
    INFINITE_DISCOUNTED = "infinite_discounted"


class Information(str, Enum):
    ORDINAL = "ordinal"
    CARDINAL = "cardinal"


class Payoff(str, Enum):
    BEST_OR_NOTHING = "best_or_nothing"
    COST_OF_SEARCH = "cost_of_search"
    RUIN_RISK = "ruin_risk"
    AVERAGE_RANK = "average_rank"
    DURATION = "duration"
    MULTIATTRIBUTE = "multiattribute"
    DISCOUNTED_RETURN = "discounted_return"


class RiskAttitude(str, Enum):
    AVERSE = "averse"
    NEUTRAL = "neutral"
    PRONE = "prone"


@dataclass
class AttributeRange:
    """Invariant 5: a scaling constant is meaningless without its assessed range."""
    name: str
    worst: float
    best: float
    monotonic_increasing: bool = True


@dataclass
class IndependenceTest:
    """Invariant 3: a recorded, verified test — never a bare boolean."""
    pair: tuple[str, str]
    method: str  # "flip_test" | "fractile" | ...
    passed: bool
    responses: list[Any] = field(default_factory=list)
    notes: str = ""


@dataclass
class InputContract:
    job: Optional[Job] = None

    # 1. Horizon
    horizon: Optional[Horizon] = None
    n: Optional[int] = None
    n_max: Optional[int] = None
    stop_prob_per_step: Optional[float] = None
    gamma: Optional[float] = None

    # 2. Alternatives / states / actions
    alternatives: Optional[Sequence[Any]] = None
    states: Optional[Sequence[Any]] = None
    actions: Optional[Sequence[Any]] = None

    # 3. Objective hierarchy and ranges
    attributes: Optional[list[AttributeRange]] = None
    payoff: Optional[Payoff] = None

    # 4. Independence
    independence_tests: Optional[list[IndependenceTest]] = None
    scaling_constants: Optional[dict[str, float]] = None

    # 5. Uncertainty
    information: Optional[Information] = None
    transition: Optional[Callable | dict] = None
    reward: Optional[Callable | dict] = None
    observation_model: Optional[Callable | dict] = None
    prior_belief: Optional[dict] = None
    observations: Optional[list] = None
    markov_verified: Optional[bool] = None

    # 6. Search costs / recall / rejection
    search_cost: Optional[float] = None
    recall_allowed: Optional[bool] = None
    recall_accept_prob: Optional[float] = None
    rejection_prob: Optional[float] = None

    # 6b. Ruin-risk (burglar) parameters — c01 §11. Required when payoff == RUIN_RISK.
    ruin_success_prob: Optional[float] = None   # q: per-trial probability of success
    ruin_mean_gain: Optional[float] = None      # m: average gain per successful trial

    # 7. Risk attitude
    risk_attitude: Optional[RiskAttitude] = None
    risk_varies_with_level: Optional[str] = None

    # 8. Compute budget
    exact_finite_n: bool = True  # default: exact, NOT asymptotic. Closes D-14.
    k_max: int = 1000
    tolerance: float = 1e-6
    mcts_simulations: Optional[int] = None
    search_depth: Optional[int] = None

    # Divergence flag — MUST be explicitly elicited, never defaulted. Closes D-08.
    payoff_diverges: Optional[bool] = None
