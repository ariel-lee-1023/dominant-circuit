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
class IndependenceAssumption:
    """Records a single verified (or hypothesized) independence claim.
    kind is either 'preferential' (ordinal, certainty case) or 'utility'
    (cardinal, uncertainty case), matching Sections 3.6 and 5.1.

    Transcribed from c02 §7.3 — the authoritative structure.
    """
    subset: frozenset       # the attribute subset Y
    complement: frozenset   # the complementary attribute subset Z
    kind: str               # 'preferential' | 'utility'
    verified: bool = False  # True only after an elicitation test confirms it
    evidence: str = ""      # description of the indifference test used


@dataclass
class IndependenceTest:
    """DEPRECATED. Superseded by IndependenceAssumption (c02 §7.3), which the
    corpus defines as the authoritative structure.

    This type records an unordered `pair` with no subset/complement distinction,
    so it cannot express which side of a claim was verified. It is retained for
    one release; `InputContract` converts it on construction.
    """
    pair: tuple[str, str]
    method: str  # "flip_test" | "fractile" | ...
    passed: bool
    responses: list[Any] = field(default_factory=list)
    notes: str = ""

    def to_assumptions(self, kind: str) -> list[IndependenceAssumption]:
        """Lossy legacy conversion.

        `pair` is unordered and carries no subset/complement direction, so the
        only faithful reading of "the pair {a, b} passed an independence test"
        is that both directions hold: {a} independent of {b} AND {b} of {a}.
        Both are emitted, each carrying `verified=self.passed`.
        """
        a, b = self.pair
        return [
            IndependenceAssumption(
                subset=frozenset({a}), complement=frozenset({b}), kind=kind,
                verified=self.passed,
                evidence=f"legacy IndependenceTest(method={self.method!r}) {self.notes}".strip(),
            ),
            IndependenceAssumption(
                subset=frozenset({b}), complement=frozenset({a}), kind=kind,
                verified=self.passed,
                evidence=f"legacy IndependenceTest(method={self.method!r}) {self.notes}".strip(),
            ),
        ]


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
    independence_assumptions: Optional[list[IndependenceAssumption]] = None
    independence_tests: Optional[list[IndependenceTest]] = None  # DEPRECATED, converted below
    scaling_constants: Optional[dict[str, float]] = None

    # 4b. Recorded flip test (c02 §7.5). `flip_test_performed` is a separate flag
    # because `preferred_pairing=None` is itself a meaningful answer ("indifferent",
    # implying the additive form) and must not be confused with "never asked".
    flip_test_performed: bool = False
    flip_test_preferred_pairing: Optional[str] = None  # None | 'straight' | 'crossed'

    # 5. Uncertainty
    information: Optional[Information] = None
    # Percentile scores in [0,1], one per candidate in arrival order. Only
    # meaningful under Information.CARDINAL (c01 §6).
    scores: Optional[Sequence[float]] = None
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

    def __post_init__(self) -> None:
        # Migrate the deprecated IndependenceTest list onto the corpus structure.
        # `[]` is elicited data ("asked, nothing verified") and must survive as `[]`,
        # not collapse to None — that distinction is what routes an empty registry to
        # Stage 2's IndependenceNotVerified instead of Stage 1's ContractIncomplete.
        if self.independence_assumptions is None and self.independence_tests is not None:
            kind = self.independence_kind
            converted: list[IndependenceAssumption] = []
            for test in self.independence_tests:
                converted.extend(test.to_assumptions(kind))
            self.independence_assumptions = converted

    @property
    def job_is_under_uncertainty(self) -> bool:
        """A risk attitude is only assessable against lotteries, so its presence is
        the contract's signal that the multiobjective problem is the uncertainty
        case (c02 §5.1 utility independence) rather than the certainty case
        (c02 §3.3 preferential independence)."""
        return self.risk_attitude is not None

    @property
    def independence_kind(self) -> str:
        return "utility" if self.job_is_under_uncertainty else "preferential"
