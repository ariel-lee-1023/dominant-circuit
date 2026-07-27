"""Engine B — Decisions with Multiple Objectives (Cluster 02)."""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence

from ..core.contract import InputContract, AttributeRange, IndependenceTest, Job
from ..core.errors import IndependenceNotVerified, PreconditionViolation, UnclassifiedVariant
from ..core.report import OutputReport, AuditResult, InvariantResult, SensitivityEntry


def dominates(a: Sequence[float], b: Sequence[float], increasing: Sequence[bool]) -> bool:
    weakly = True
    strictly = False
    for ai, bi, inc in zip(a, b, increasing):
        if inc:
            if ai < bi:
                weakly = False
                break
            if ai > bi:
                strictly = True
        else:
            if ai > bi:
                weakly = False
                break
            if ai < bi:
                strictly = True
    return weakly and strictly


def efficient_frontier(
    alternatives: list[dict[str, Any]],
    attributes: list[AttributeRange],
) -> list[dict[str, Any]]:
    names = [a.name for a in attributes]
    increasing = [a.monotonic_increasing for a in attributes]
    frontier = []
    for cand in alternatives:
        vec = [float(cand.get(n, 0)) for n in names]
        dominated = False
        for other in alternatives:
            if other is cand:
                continue
            ovec = [float(other.get(n, 0)) for n in names]
            if dominates(ovec, vec, increasing):
                dominated = True
                break
        if not dominated:
            frontier.append(cand)
    return frontier


def _normalize(raw: float, attr: AttributeRange) -> float:
    lo, hi = attr.worst, attr.best
    if abs(hi - lo) < 1e-15:
        raise PreconditionViolation(f"Degenerate range for {attr.name}")
    if attr.monotonic_increasing:
        u = (raw - lo) / (hi - lo)
    else:
        u = (hi - raw) / (hi - lo)
    return max(0.0, min(1.0, u))


def additive_value(
    levels: dict[str, float],
    attributes: list[AttributeRange],
    weights: dict[str, float],
    component_utils: Optional[dict[str, float]] = None,
) -> float:
    s = 0.0
    for attr in attributes:
        w = weights[attr.name]
        if component_utils and attr.name in component_utils:
            u = component_utils[attr.name]
        else:
            u = _normalize(levels[attr.name], attr)
        s += w * u
    return s


def solve_multiplicative_k(k_i: Sequence[float], tol: float = 1e-12) -> float:
    total = sum(k_i)
    if abs(total - 1.0) < 1e-12:
        return 0.0

    def f(k: float) -> float:
        prod = 1.0
        for ki in k_i:
            prod *= 1.0 + k * ki
        return 1.0 + k - prod

    if total > 1.0:
        lo, hi = -1.0 + 1e-12, -1e-12
    else:
        lo, hi = 1e-12, 1e6

    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0 and total < 1.0:
        for _ in range(40):
            hi *= 2
            fhi = f(hi)
            if flo * fhi <= 0:
                break
        else:
            raise PreconditionViolation("No consistent k for given scaling constants.")

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if abs(fm) < tol or abs(hi - lo) < tol:
            return mid
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def multiplicative_utility(
    levels: dict[str, float],
    attributes: list[AttributeRange],
    k_i: dict[str, float],
    k: float,
    component_utils: Optional[dict[str, float]] = None,
) -> float:
    if abs(k) < 1e-15:
        return additive_value(levels, attributes, k_i, component_utils)
    prod = 1.0
    for attr in attributes:
        if component_utils and attr.name in component_utils:
            u = component_utils[attr.name]
        else:
            u = _normalize(levels[attr.name], attr)
        prod *= 1.0 + k * k_i[attr.name] * u
    return (prod - 1.0) / k


def solve_multiobjective(contract: InputContract) -> OutputReport:
    attributes = contract.attributes or []
    if not attributes:
        raise PreconditionViolation("attributes required", field="attributes")

    tests = contract.independence_tests or []
    if not any(t.passed for t in tests):
        raise IndependenceNotVerified(
            "Independence not verified. Flip-test (or equivalent) required before any multiattribute form.",
            remedy="Run flip test (c02 §5.2) and record IndependenceTest(passed=True).",
            field="independence_tests",
        )

    weights = contract.scaling_constants or {}
    if not weights:
        raise PreconditionViolation("scaling_constants required", field="scaling_constants")

    names = {a.name for a in attributes}
    for key in weights:
        if key not in names:
            raise PreconditionViolation(
                f"Scaling constant '{key}' has no attached AttributeRange.",
                field="scaling_constants",
            )

    k_list = [weights[a.name] for a in attributes]
    total = sum(k_list)

    if abs(total - 1.0) < 1e-9:
        form = "additive"
        k = 0.0
        formula_name = "Additive Multiattribute Utility"
        latex = r"u(x) = \sum_i k_i u_i(x_i)"
        cite = "c02 §5.3 (additive special case)"
    else:
        form = "multiplicative"
        k = solve_multiplicative_k(k_list)
        formula_name = "Multiplicative Multiattribute Utility"
        latex = r"1 + k\,u(x) = \prod_i (1 + k\,k_i\,u_i(x_i))"
        cite = "c02 §5.3"

    alts = list(contract.alternatives or [])
    scored: list[dict[str, Any]] = []
    best = None
    best_score = -math.inf

    if alts and all(isinstance(a, dict) for a in alts):
        frontier = efficient_frontier(alts, attributes)
        for alt in frontier:
            levels = {attr.name: float(alt.get(attr.name, 0)) for attr in attributes}
            label = alt.get("name", str(alt))
            if form == "additive":
                score = additive_value(levels, attributes, weights)
            else:
                score = multiplicative_utility(levels, attributes, weights, k)
            scored.append({"name": label, "utility": score, "levels": levels})
            if score > best_score:
                best_score = score
                best = label

    decision = {
        "form": form,
        "k": k,
        "best_alternative": best,
        "best_utility": best_score if best is not None else None,
        "ranked": sorted(scored, key=lambda x: -x["utility"]),
    }

    assumptions = {
        "form": form,
        "independence_verified": True,
        "n_attributes": len(attributes),
        "sum_k_i": total,
        "k": k,
        "attribute_ranges": {
            a.name: {"worst": a.worst, "best": a.best, "increasing": a.monotonic_increasing}
            for a in attributes
        },
        "scaling_constants": weights,
    }

    n_params = len(attributes)
    n_eq = len(tests)
    overdet = n_eq > max(1, n_params - 1)

    return OutputReport(
        decision=decision,
        formula_name=formula_name,
        formula_latex=latex,
        citation=cite,
        numeric={
            "k": k,
            "sum_k_i": total,
            "best_utility": best_score if best is not None else float("nan"),
        },
        assumptions=assumptions,
        sensitivity=[
            SensitivityEntry(
                assumption="independence_tests",
                perturbation="passed → failed",
                new_decision="REFUSED (IndependenceNotVerified)",
                decision_changed=True,
                fragility="critical",
            ),
            SensitivityEntry(
                assumption="sum k_i",
                perturbation=f"{total:.4f}",
                new_decision="additive" if abs(total - 1) < 1e-9 else "multiplicative",
                decision_changed=False,
                fragility="fragile",
            ),
        ],
        audit=AuditResult(results=[
            InvariantResult("INV-3", "independence_verified", True, message="Flip-test recorded"),
            InvariantResult("INV-5", "range_fixed_weights", True, message="Every k_i has AttributeRange"),
            InvariantResult(
                "INV-7", "overdetermination", overdet,
                message=f"{n_eq} tests vs {n_params} parameters" if overdet
                else f"Underdetermined: {n_eq} tests for {n_params} parameters",
            ),
            InvariantResult(
                "INV-weight-sum", "form_consistency", True,
                message=f"form={form}, k={k:.6g}, Σk_i={total:.6g}",
            ),
        ]),
    )
