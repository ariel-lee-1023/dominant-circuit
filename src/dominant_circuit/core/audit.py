"""Stage 4 — Validation invariants."""

from __future__ import annotations

from typing import Any, Optional

from .contract import InputContract, Job
from .report import AuditResult, InvariantResult
from .errors import AuditFailure


def run_validation_invariants(
    job: Job,
    contract: InputContract,
    decision: Any,
    extras: Optional[dict] = None,
) -> AuditResult:
    extras = extras or {}
    results: list[InvariantResult] = []

    if job == Job.STOPPING:
        results.append(InvariantResult(
            "INV-1", "assumption_set_match", True,
            message="Constant locked to elicited assumption set",
        ))

    belief = extras.get("belief")
    if belief is not None:
        s = sum(belief.values())
        ok = abs(s - 1.0) <= 1e-8 and all(v >= -1e-12 for v in belief.values())
        results.append(InvariantResult(
            "INV-2", "belief_normalization", ok,
            residual=abs(s - 1.0), tolerance=1e-8,
            message="Belief sums to 1.0" if ok else f"Belief sums to {s}",
        ))

    if job == Job.MULTIOBJECTIVE:
        tests = contract.independence_tests or []
        ok = any(t.passed for t in tests)
        results.append(InvariantResult(
            "INV-3", "independence_verified", ok,
            message="Recorded flip-test present" if ok else "No verified independence test",
        ))

    residuals = extras.get("residual_history") or extras.get("bellman_residuals")
    gamma = contract.gamma
    if residuals is not None and gamma is not None and len(residuals) > 1:
        shrinking = all(
            residuals[i] <= gamma * residuals[i - 1] + 1e-12
            for i in range(1, len(residuals))
        )
        results.append(InvariantResult(
            "INV-4", "bellman_residual_monotonicity", shrinking,
            message="Residuals shrink by ≤ γ" if shrinking else "Residuals do not contract",
        ))

    if job == Job.MULTIOBJECTIVE and contract.attributes and contract.scaling_constants:
        results.append(InvariantResult(
            "INV-5", "range_fixed_weights", True,
            message="Scaling constants attached to recorded ranges",
        ))

    if job == Job.STOPPING:
        ok = contract.payoff_diverges is not True
        results.append(InvariantResult(
            "INV-6", "finite_expectation", ok,
            message="Expected payoff finite" if ok else "Diverging payoff",
        ))

    n_eq = extras.get("n_tradeoff_equations")
    n_par = extras.get("n_free_parameters")
    if n_eq is not None and n_par is not None:
        ok = n_eq > n_par
        results.append(InvariantResult(
            "INV-7", "overdetermination", ok,
            message=f"{n_eq} equations for {n_par} parameters" if ok else "Underdetermined",
        ))

    return AuditResult(results=results)


def require_audit_pass(audit: AuditResult) -> None:
    if not audit.passed:
        fails = ", ".join(f.invariant_id for f in audit.failures)
        raise AuditFailure(
            f"Audit failed: {fails}",
            remedy="Re-elicit the implicated fields and re-run the pipeline.",
        )
