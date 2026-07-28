"""
Dominant-Circuit — pure, non-interactive decision-mechanics library.

Host AI owns conversation. This package is the physics engine.
"""

from .core.contract import (
    InputContract, Job, Horizon, Information, Payoff, RiskAttitude,
    AttributeRange, IndependenceTest, IndependenceAssumption,
)
from .core.report import OutputReport, AuditResult, InvariantResult, SensitivityEntry
from .core.errors import (
    DominantCircuitError, ContractIncomplete, PreconditionViolation,
    NoOptimalStoppingRuleExists, IndependenceNotVerified, NonMarkovProcess,
    UnclassifiedVariant, AuditFailure, NotInCorpus,
)
from .core.elicit import missing_fields, next_question, require_complete
from .core.verify import verify_preconditions
from .core.audit import run_validation_invariants
from .core.dispatch import dispatch
from .engines.stopping import optimal_cutoff, asymptotic_cutoff, parking_cutoff
from .engines.multiobjective import (
    solve_multiplicative_k, additive_value, multiplicative_utility,
    mutual_independence_holds, uncovered_independence_subsets,
    run_flip_test, FlipTestResult, efficient_frontier, dominates,
)
from .engines.sequential import belief_update, value_iteration

__version__ = "0.3.0"

__all__ = [
    "dispatch",
    "InputContract",
    "Job", "Horizon", "Information", "Payoff", "RiskAttitude",
    "AttributeRange", "IndependenceTest", "IndependenceAssumption",
    "OutputReport", "AuditResult", "InvariantResult", "SensitivityEntry",
    "DominantCircuitError", "ContractIncomplete", "PreconditionViolation",
    "NoOptimalStoppingRuleExists", "IndependenceNotVerified", "NonMarkovProcess",
    "UnclassifiedVariant", "AuditFailure", "NotInCorpus",
    "missing_fields", "next_question", "require_complete",
    "verify_preconditions",
    "run_validation_invariants",
    "optimal_cutoff", "asymptotic_cutoff", "parking_cutoff",
    "solve_multiplicative_k", "additive_value", "multiplicative_utility",
    "mutual_independence_holds", "uncovered_independence_subsets",
    "run_flip_test", "FlipTestResult", "efficient_frontier", "dominates",
    "belief_update", "value_iteration",
]
