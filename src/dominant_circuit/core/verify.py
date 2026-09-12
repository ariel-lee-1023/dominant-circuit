"""Stage 2 — Hard precondition blockers. No silent defaults."""

from __future__ import annotations
import math

from .contract import InputContract, Job, Payoff
from .errors import (
    PreconditionViolation, UnclassifiedVariant,
    NoOptimalStoppingRuleExists,
    IndependenceNotVerified,
    NonMarkovProcess,
)
from .elicit import require_complete


def verify_preconditions(contract: InputContract) -> None:
    require_complete(contract)
    if contract.schema_version != 2:
        raise PreconditionViolation("Unsupported contract schema; migrate explicitly",field="schema_version")
    dynamic = any(getattr(contract,n) is not None for n in ('states','actions','transition','reward','prior_belief','gamma'))
    if (contract.job != Job.SEQUENTIAL and dynamic) or (contract.job != Job.MULTIOBJECTIVE and contract.attributes is not None):
        raise UnclassifiedVariant("No implemented semantics compose these model inputs",field="job",remedy="Separate the questions or provide a supported interface.")
    if contract.job != Job.MULTIOBJECTIVE and contract.constraints:
        raise UnclassifiedVariant("Explicit constraint predicates are supported for static alternatives only",field="constraints")


    if contract.job == Job.STOPPING:
        for name in ('n','n_max'):
            value = getattr(contract,name)
            if value is not None and (isinstance(value,bool) or not isinstance(value,int) or value < 1):
                raise PreconditionViolation("Positive integer pool size required",field=name)
        for name in ('recall_allowed','payoff_diverges'):
            value = getattr(contract,name)
            if value is not None and not isinstance(value,bool):
                raise PreconditionViolation("Explicit boolean required",field=name)
        for name in ('rejection_prob','recall_accept_prob','stop_prob_per_step','ruin_success_prob'):
            value = getattr(contract,name)
            if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value) or not 0 <= value <= 1):
                raise PreconditionViolation("Finite probability in [0,1] required",field=name)
        for name in ('search_cost','ruin_mean_gain'):
            value = getattr(contract,name)
            if value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0):
                raise PreconditionViolation("Finite nonnegative quantity required",field=name)
        if contract.scores is not None and (contract.n is None or len(contract.scores) != contract.n or any(
            not isinstance(v,(int,float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in contract.scores)):
            raise PreconditionViolation("One finite percentile in [0,1] per candidate required",field="scores")
        if contract.payoff_diverges is True:
            raise NoOptimalStoppingRuleExists(
                "Expected reward at the best conceivable stopping point is infinite. "
                "No optimal stopping rule exists.",
                remedy="Switch to a bankroll-fraction framework (e.g. Kelly criterion).",
                field="payoff_diverges",
            )

    if contract.job == Job.MULTIOBJECTIVE:
        # Deferred import: engines must not be imported by core at module load.
        from ..engines.multiobjective import (
            mutual_independence_holds, uncovered_independence_subsets,
        )

        attrs = frozenset(a.name for a in (contract.attributes or []))
        kind = contract.independence_kind
        if not mutual_independence_holds(contract.independence_assumptions, attrs, kind):
            uncovered = uncovered_independence_subsets(
                contract.independence_assumptions, attrs, kind
            )
            missing_desc = sorted("{" + ", ".join(sorted(s)) + "}" for s in uncovered)
            raise IndependenceNotVerified(
                "Mutual independence is not covered by the assumption registry: "
                f"missing subsets {missing_desc}.",
                remedy="Elicit and record an IndependenceAssumption for each listed subset (c02 §7.3).",
                field="independence_assumptions",
            )
        if contract.attributes:
            for attr in contract.attributes:
                if abs(attr.best - attr.worst) < 1e-15:
                    raise PreconditionViolation(
                        f"Attribute '{attr.name}' has degenerate range.",
                        field="attributes",
                    )
        if contract.scaling_constants and contract.attributes:
            names = {a.name for a in contract.attributes}
            for k in contract.scaling_constants:
                if k not in names:
                    raise PreconditionViolation(
                        f"Scaling constant '{k}' has no attached AttributeRange.",
                        remedy="Record an AttributeRange for every k_i (Invariant 5).",
                        field="scaling_constants",
                    )

    if contract.job == Job.SEQUENTIAL:
        if contract.markov_verified is False:
            raise NonMarkovProcess(
                "The transition model must satisfy the Markov property. "
                "If the process depends on deep history, augment the state space.",
                remedy="Redefine the state so that next-state depends only on current state + action, then set markov_verified=True.",
                field="markov_verified",
            )
        if contract.gamma is not None and not (0.0 <= contract.gamma < 1.0):
            raise PreconditionViolation(
                f"Discount factor γ must satisfy 0 ≤ γ < 1 for Bellman contraction. Got γ={contract.gamma}.",
                field="gamma",
            )
