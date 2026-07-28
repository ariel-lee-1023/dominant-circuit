"""Stage 2 — Hard precondition blockers. No silent defaults."""

from __future__ import annotations

from .contract import InputContract, Job, Payoff
from .errors import (
    PreconditionViolation,
    NoOptimalStoppingRuleExists,
    IndependenceNotVerified,
    NonMarkovProcess,
)
from .elicit import require_complete


def verify_preconditions(contract: InputContract) -> None:
    require_complete(contract)

    if contract.job == Job.STOPPING:
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
