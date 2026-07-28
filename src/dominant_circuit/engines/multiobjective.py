"""Engine B — Decisions with Multiple Objectives (Cluster 02)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Optional, Sequence

from ..core.audit import check_range_fixed_weights
from ..core.contract import (
    InputContract, AttributeRange, IndependenceAssumption, IndependenceTest, Job,
)
from ..core.errors import IndependenceNotVerified, PreconditionViolation, UnclassifiedVariant
from ..core.report import OutputReport, AuditResult, InvariantResult, SensitivityEntry


# --- Independence registry coverage (c02 §7.3) ------------------------------------

def required_independence_subsets(all_attrs: frozenset) -> set[frozenset]:
    """Every proper nonempty subset of the attribute set. c02 §7.3."""
    attrs = list(all_attrs)
    needed: set[frozenset] = set()
    for r in range(1, len(attrs)):
        for combo in combinations(attrs, r):
            needed.add(frozenset(combo))
    return needed


def _verified_subsets(assumptions: Optional[Sequence[IndependenceAssumption]],
                      all_attrs: frozenset, kind: str) -> set[frozenset]:
    return {
        a.subset for a in (assumptions or [])
        if a.kind == kind and a.verified and a.complement == all_attrs - a.subset
    }


def uncovered_independence_subsets(
    assumptions: Optional[Sequence[IndependenceAssumption]],
    all_attrs: frozenset,
    kind: str,
) -> set[frozenset]:
    """The proper nonempty subsets the registry does not cover. Empty == mutual
    independence is established by the registry."""
    verified = _verified_subsets(assumptions, all_attrs, kind)
    needed = required_independence_subsets(all_attrs)

    if len(all_attrs) == 3:
        # c02 §3.4: for n = 3, pairwise preferential independence -- each 2-element
        # subset independent of its complementary singleton -- is equivalent to
        # mutual preferential independence, so the pairwise checks suffice.
        pairwise = {s for s in needed if len(s) == 2}
        if pairwise.issubset(verified):
            return set()
        return pairwise - verified

    return needed - verified


def mutual_independence_holds(
    assumptions: Optional[Sequence[IndependenceAssumption]],
    all_attrs: frozenset,
    kind: str,
) -> bool:
    """Mutual (preferential or utility) independence requires every proper
    nonempty subset to be independent of its complement (c02 §7.3). This checks
    that the assumption registry actually covers that requirement -- it does not
    itself elicit anything."""
    return not uncovered_independence_subsets(assumptions, all_attrs, kind)


def _format_subsets(subsets: set[frozenset]) -> list[str]:
    return sorted("{" + ", ".join(sorted(s)) + "}" for s in subsets)


# --- Flip test (c02 §7.5) ---------------------------------------------------------

@dataclass
class FlipTestResult:
    indifferent: bool         # True if decision maker was indifferent between the two lotteries
    implied_form: str         # 'additive' or 'multiplicative'
    k_yz_sign: Optional[int]  # +1, -1, 0, or None if not applicable


def run_flip_test(preferred_pairing: Optional[str],
                  mutual_utility_independence_verified: bool = False) -> FlipTestResult:
    """Operationalizes the book's discriminating corollary (c02 §5.2, §5.3,
    Theorem 6.1 corollary): offer two 50-50 lotteries built from the same
    consequences but with attributes 'straight' vs. 'crossed' across the pairing,
    and record whether the decision maker is indifferent (additive) or has a
    strict preference (multiplicative).

    This test's conclusion is conditional on mutual utility independence already
    holding: the representation from which k_YZ is defined only exists under that
    structure, so the test cannot be interpreted, and must not be run, until
    mutual_utility_independence_verified is True. The test only distinguishes
    additive from multiplicative *within* that structure; it does not establish
    the independence structure itself.

    preferred_pairing: None if indifferent; 'straight' if the pairing
    (high,high)/(low,low) is preferred; 'crossed' if (high,low)/(low,high).
    """
    if not mutual_utility_independence_verified:
        raise ValueError(
            "Mutual utility independence must be verified before the flip "
            "test's conclusion about additive vs. multiplicative form is "
            "meaningful (c02 §5.1, §5.3)."
        )
    if preferred_pairing is None:
        return FlipTestResult(indifferent=True, implied_form="additive", k_yz_sign=0)
    if preferred_pairing == "straight":
        return FlipTestResult(indifferent=False, implied_form="multiplicative", k_yz_sign=1)
    if preferred_pairing == "crossed":
        return FlipTestResult(indifferent=False, implied_form="multiplicative", k_yz_sign=-1)
    raise ValueError("preferred_pairing must be None, 'straight', or 'crossed'.")


def check_independence_and_form(contract: InputContract,
                                flip_result: Optional[FlipTestResult],
                                k_sum: float) -> InvariantResult:
    """INV-3. (a) registry coverage holds; (b) the recorded flip test's implied_form
    agrees with the form implied by sum(k_i). Disagreement means the elicitation is
    internally inconsistent — surface it, do not average it away (c02 §7.8)."""
    all_attrs = frozenset(a.name for a in (contract.attributes or []))
    kind = contract.independence_kind
    uncovered = uncovered_independence_subsets(
        contract.independence_assumptions, all_attrs, kind
    )

    form_from_k = "additive" if abs(k_sum - 1.0) < 1e-9 else "multiplicative"

    problems: list[str] = []
    if uncovered:
        problems.append(
            f"{kind} independence registry does not cover {_format_subsets(uncovered)} (c02 §7.3)"
        )
    if flip_result is not None and flip_result.implied_form != form_from_k:
        problems.append(
            f"form disagreement: recorded flip test implies {flip_result.implied_form} "
            f"(c02 §7.5) but Σk_i={k_sum:.6g} implies {form_from_k} (c02 §5.3). "
            "Σk_i = 1 ⟺ k = 0 ⟺ additive, so these cannot both be right"
        )

    passed = not problems
    if passed:
        detail = f"form={form_from_k}, Σk_i={k_sum:.6g}"
        if flip_result is not None:
            detail += f", flip test agrees (k_YZ sign {flip_result.k_yz_sign})"
        else:
            detail += ", no flip test recorded"
        message = f"Mutual {kind} independence covered by the registry; {detail}"
    else:
        message = "; ".join(problems)

    return InvariantResult("INV-3", "independence_and_form", passed, message=message)


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

    all_attrs = frozenset(a.name for a in attributes)
    kind = contract.independence_kind
    assumptions_registry = contract.independence_assumptions
    uncovered = uncovered_independence_subsets(assumptions_registry, all_attrs, kind)
    if uncovered:
        raise IndependenceNotVerified(
            "Mutual independence is not covered by the assumption registry: "
            f"missing subsets {_format_subsets(uncovered)}.",
            remedy="Elicit and record an IndependenceAssumption for each listed subset (c02 §7.3).",
            field="independence_assumptions",
        )

    # The flip test discriminates additive vs. multiplicative *within* an already
    # verified independence structure (c02 §7.5); it never establishes it.
    flip_result: Optional[FlipTestResult] = None
    if contract.flip_test_performed:
        flip_result = run_flip_test(
            contract.flip_test_preferred_pairing,
            mutual_utility_independence_verified=True,
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

    registry = assumptions_registry or []
    assumptions = {
        "form": form,
        "independence_kind": kind,
        "independence_verified": True,
        "independence_subsets_verified": _format_subsets(
            _verified_subsets(registry, all_attrs, kind)
        ),
        "flip_test_performed": contract.flip_test_performed,
        "flip_test_implied_form": flip_result.implied_form if flip_result else None,
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
    n_eq = len(registry)
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
                assumption="independence_assumptions",
                perturbation="any covered subset → unverified",
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
            check_independence_and_form(contract, flip_result, total),
            check_range_fixed_weights(contract),
            InvariantResult(
                "INV-7", "overdetermination", overdet,
                message=f"{n_eq} recorded assumptions vs {n_params} parameters" if overdet
                else f"Underdetermined: {n_eq} recorded assumptions for {n_params} parameters",
            ),
        ]),
    )
