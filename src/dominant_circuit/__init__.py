"""
Dominant-Circuit — pure, non-interactive decision-mechanics library.

Host AI owns conversation. This package is the physics engine.
"""

from .core.contract import (
    InputContract, Job, Horizon, Information, Payoff, RiskAttitude,
    AttributeRange, IndependenceTest, IndependenceAssumption,
)
from .core.report import (
    OutputReport, AuditResult, InvariantResult, SensitivityEntry,
    PerturbationTerm, relative_shift,
    ORDER_ZERO, ORDER_FIRST, ORDER_OVERTURN, ORDER_HARD, ORDER_DROPPED,
)
from .core.errors import (
    DominantCircuitError, ContractIncomplete, PreconditionViolation,
    NoOptimalStoppingRuleExists, IndependenceNotVerified, NonMarkovProcess,
    UnclassifiedVariant, AuditFailure, NotInCorpus,
)
from .core.elicit import missing_fields, next_question, require_complete, classify_job, QUESTION_BANK
from .core.verify import verify_preconditions
from .core.audit import run_validation_invariants, check_range_fixed_weights, INVARIANT_FIELDS
from .core.dispatch import dispatch
from .engines.stopping import (
    optimal_cutoff, asymptotic_cutoff, parking_cutoff, parking_cutoff_exact,
    threshold_percentile, threshold_rule, threshold_schedule,
    cost_aware_threshold, burglar_ceiling,
    cutoff_unknown_horizon_uniform, cutoff_stochastic_stop,
    cutoff_with_recall, cutoff_with_rejection,
    Calibration, CALIBRATIONS, check_assumption_set_match,
)
from .engines.multiobjective import (
    solve_multiplicative_k, additive_value, multiplicative_utility,
    mutual_independence_holds, uncovered_independence_subsets,
    run_flip_test, FlipTestResult, efficient_frontier, dominates,
    dominance_screen, check_independence_and_form, required_independence_subsets,
    independence_questions, record_independence, FLIP_TEST_QUESTION,
)
from .engines.sequential import belief_update, value_iteration

__version__ = "0.4.0"

__all__ = [
    "dispatch",
    "InputContract",
    "Job", "Horizon", "Information", "Payoff", "RiskAttitude",
    "AttributeRange", "IndependenceTest", "IndependenceAssumption",
    "OutputReport", "AuditResult", "InvariantResult", "SensitivityEntry",
    "PerturbationTerm", "relative_shift",
    "ORDER_ZERO", "ORDER_FIRST", "ORDER_OVERTURN", "ORDER_HARD", "ORDER_DROPPED",
    "DominantCircuitError", "ContractIncomplete", "PreconditionViolation",
    "NoOptimalStoppingRuleExists", "IndependenceNotVerified", "NonMarkovProcess",
    "UnclassifiedVariant", "AuditFailure", "NotInCorpus",
    "missing_fields", "next_question", "require_complete", "classify_job", "QUESTION_BANK",
    "verify_preconditions",
    "run_validation_invariants", "check_range_fixed_weights", "INVARIANT_FIELDS",
    "optimal_cutoff", "asymptotic_cutoff", "parking_cutoff", "parking_cutoff_exact",
    "threshold_percentile", "threshold_rule", "threshold_schedule",
    "cost_aware_threshold", "burglar_ceiling",
    "cutoff_unknown_horizon_uniform", "cutoff_stochastic_stop",
    "cutoff_with_recall", "cutoff_with_rejection",
    "Calibration", "CALIBRATIONS", "check_assumption_set_match",
    "solve_multiplicative_k", "additive_value", "multiplicative_utility",
    "mutual_independence_holds", "uncovered_independence_subsets",
    "run_flip_test", "FlipTestResult", "efficient_frontier", "dominates",
    "dominance_screen", "check_independence_and_form", "required_independence_subsets",
    "independence_questions", "record_independence", "FLIP_TEST_QUESTION",
    "belief_update", "value_iteration",
]
