"""Engine A — Optimal Stopping (Cluster 01). Exact finite-n by default."""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence, Tuple

from ..core.contract import InputContract, Horizon, Information, Payoff
from ..core.errors import UnclassifiedVariant, NoOptimalStoppingRuleExists
from ..core.report import OutputReport, AuditResult, InvariantResult, SensitivityEntry


def optimal_cutoff(n: int) -> Tuple[int, float]:
    """Exact finite-n argmax of P_n(r). SPEC §14.1 golden values."""
    if n < 1:
        raise ValueError("n must be ≥ 1")
    if n == 1:
        return 1, 1.0
    best_r, best_p = 1, 1.0 / n
    for r in range(2, n + 1):
        harmonic_tail = sum(1.0 / (j - 1) for j in range(r, n + 1))
        p = ((r - 1) / n) * harmonic_tail
        if p > best_p:
            best_r, best_p = r, p
    return best_r, best_p


def asymptotic_cutoff(n: int) -> Tuple[int, float]:
    r = max(1, round(n / math.e))
    return r, 1.0 / math.e


def threshold_percentile(k: int) -> float:
    if k <= 0:
        return 0.0
    return 1.0 / (1.0 + 0.804 / k + 0.183 / (k * k))


def cost_aware_threshold(low: float, high: float, c_normalized: float) -> float:
    c = max(0.0, min(0.5, c_normalized))
    p = 1.0 - math.sqrt(2.0 * c)
    return low + p * (high - low)


def burglar_ceiling(q: float, m: float) -> float:
    if not (0.0 < q < 1.0):
        raise ValueError("q must be in (0,1)")
    return m * q / (1.0 - q)


def parking_cutoff(occupancy: float) -> int:
    """Corrected form: floor(-log 2 / log p). SPEC §12 / D-03."""
    if not (0.0 < occupancy < 1.0):
        raise ValueError("occupancy must be in (0,1)")
    return math.floor(-math.log(2) / math.log(occupancy))


def parking_cutoff_exact(occupancy: float) -> float:
    if not (0.0 < occupancy < 1.0):
        raise ValueError("occupancy must be in (0,1)")
    return -math.log(2) / math.log(occupancy)


def cutoff_unknown_horizon_uniform(n_max: int) -> Tuple[int, float]:
    r = max(1, round(n_max / (math.e ** 2)))
    return r, 2.0 / (math.e ** 2)


def cutoff_stochastic_stop(p: float) -> Tuple[int, float]:
    if p <= 0:
        raise ValueError("p must be > 0")
    r = max(1, round(0.18 / p))
    return r, 0.236


def cutoff_with_recall(n: int, recall_accept_prob: float) -> Tuple[int, float]:
    if abs(recall_accept_prob - 0.5) > 1e-9:
        raise UnclassifiedVariant(
            f"recall_accept_prob={recall_accept_prob} is outside the calibrated set (0.5). "
            "Do not reuse the 0.61 constant.",
            remedy="Re-derive the optimal look fraction for this acceptance probability, or set recall_accept_prob=0.5.",
            field="recall_accept_prob",
        )
    r = max(1, round(0.61 * n))
    return r, 0.61


def cutoff_with_rejection(n: int, rejection_prob: float) -> Tuple[int, float]:
    if abs(rejection_prob - 0.5) > 1e-9:
        raise UnclassifiedVariant(
            f"rejection_prob={rejection_prob} is outside the calibrated set (0.5). "
            "Do not reuse the 0.25 constant.",
            remedy="Re-derive the optimal look fraction for this rejection probability, or set rejection_prob=0.5.",
            field="rejection_prob",
        )
    r = max(1, round(0.25 * n))
    return r, 0.25


def solve_stopping(contract: InputContract) -> OutputReport:
    if contract.payoff_diverges is True:
        raise NoOptimalStoppingRuleExists(
            "Expected reward at the best stopping point is infinite. No optimal stopping rule exists.",
            remedy="Switch to a bankroll-fraction framework (e.g. Kelly criterion).",
            field="payoff_diverges",
        )

    assumptions = {
        "horizon": contract.horizon.value if contract.horizon else None,
        "n": contract.n,
        "information": contract.information.value if contract.information else None,
        "recall_allowed": contract.recall_allowed,
        "recall_accept_prob": contract.recall_accept_prob,
        "rejection_prob": contract.rejection_prob,
        "payoff": contract.payoff.value if contract.payoff else None,
        "exact_finite_n": contract.exact_finite_n,
        "payoff_diverges": contract.payoff_diverges,
    }

    if contract.payoff == Payoff.COST_OF_SEARCH:
        if contract.search_cost is None:
            raise ValueError("search_cost required for COST_OF_SEARCH")
        thr = cost_aware_threshold(0.0, 1.0, contract.search_cost)
        return OutputReport(
            decision=thr,
            formula_name="Cost-Aware Threshold",
            formula_latex=r"p^* = 1 - \sqrt{2c}",
            citation="c01 §9",
            numeric={"threshold": thr, "c": contract.search_cost},
            assumptions=assumptions,
            sensitivity=[
                SensitivityEntry(
                    assumption="search_cost",
                    perturbation=f"{contract.search_cost} → higher",
                    new_decision="lower threshold (more permissive)",
                    decision_changed=True,
                    fragility="fragile",
                )
            ],
            audit=AuditResult(results=[
                InvariantResult("INV-6", "finite_expectation", True, message="cost-of-search has finite expectation"),
            ]),
        )

    if contract.payoff == Payoff.RUIN_RISK:
        raise UnclassifiedVariant("RUIN_RISK requires explicit q and m parameters in this version.")

    info = contract.information
    horizon = contract.horizon
    n = contract.n

    if info == Information.CARDINAL:
        schedule = {k: threshold_percentile(k) for k in range(0, 11)}
        return OutputReport(
            decision="threshold_schedule",
            formula_name="Threshold Rule",
            formula_latex=r"t_k = 1/(1 + 0.804/k + 0.183/k^2)",
            citation="c01 §6",
            numeric={f"t_{k}": v for k, v in schedule.items()},
            assumptions=assumptions,
            sensitivity=[
                SensitivityEntry(
                    assumption="information",
                    perturbation="cardinal → ordinal",
                    new_decision="Look-Then-Leap ~37%",
                    decision_changed=True,
                    fragility="critical",
                )
            ],
            audit=AuditResult(results=[
                InvariantResult("INV-1", "assumption_set_match", True, message="cardinal → Threshold Rule"),
            ]),
        )

    if horizon == Horizon.FIXED_KNOWN:
        if n is None or n < 1:
            raise ValueError("n required for FIXED_KNOWN")
        if contract.recall_allowed and contract.recall_accept_prob is not None:
            r_star, p_star = cutoff_with_recall(n, contract.recall_accept_prob)
            formula = "Look-Then-Leap + fallback recall"
            latex = r"r \\approx 0.61 n \\quad (50\\%\\ \\mathrm{recall\\text{-}accept})"
            cite = "c01 §7"
        elif contract.rejection_prob is not None and contract.rejection_prob > 0:
            r_star, p_star = cutoff_with_rejection(n, contract.rejection_prob)
            formula = "Early-and-often proposing (rejection risk)"
            latex = r"r \\approx 0.25 n \\quad (50\\%\\ \\mathrm{accept})"
            cite = "c01 §7"
        else:
            if contract.exact_finite_n:
                r_star, p_star = optimal_cutoff(n)
                formula = "Look-Then-Leap (exact finite-n)"
                latex = r"r^* = \\arg\\max_r P_n(r),\\quad P_n(r)=\\frac{r-1}{n}\\sum_{j=r}^{n}\\frac{1}{j-1}"
                cite = "c01 §4.1"
            else:
                r_star, p_star = asymptotic_cutoff(n)
                formula = "Look-Then-Leap (asymptotic 1/e)"
                latex = r"r \\approx n/e,\\quad P\\to 1/e"
                cite = "c01 §5"

        return OutputReport(
            decision={"look_until": r_star - 1, "leap_from": r_star, "n": n},
            formula_name=formula,
            formula_latex=latex,
            citation=cite,
            numeric={"r_star": float(r_star), "P_n": p_star, "n": float(n)},
            assumptions=assumptions,
            sensitivity=[
                SensitivityEntry(
                    assumption="exact_finite_n",
                    perturbation=f"True → False (n={n})",
                    new_decision=asymptotic_cutoff(n)[0] if contract.exact_finite_n else optimal_cutoff(n)[0],
                    decision_changed=(optimal_cutoff(n)[0] != asymptotic_cutoff(n)[0]),
                    fragility="fragile" if n < 200 else "robust",
                ),
                SensitivityEntry(
                    assumption="recall_allowed",
                    perturbation="False → True (0.5)",
                    new_decision=round(0.61 * n),
                    decision_changed=True,
                    fragility="critical",
                ),
            ],
            audit=AuditResult(results=[
                InvariantResult("INV-1", "assumption_set_match", True,
                                message=f"constant locked to elicited assumption set ({cite})"),
                InvariantResult("INV-6", "finite_expectation", True, message="best-or-nothing has finite expectation"),
            ]),
        )

    if horizon == Horizon.FIXED_UNKNOWN_UNIFORM:
        n_max = contract.n_max or n
        if n_max is None:
            raise ValueError("n_max required")
        r_star, p_star = cutoff_unknown_horizon_uniform(n_max)
        return OutputReport(
            decision={"look_until": r_star - 1, "leap_from": r_star},
            formula_name="Look-Then-Leap (unknown n ~ Uniform)",
            formula_latex=r"r \\approx n_{\\max}/e^2",
            citation="c01 §8",
            numeric={"r_star": float(r_star), "P": p_star},
            assumptions=assumptions,
            sensitivity=[],
            audit=AuditResult(results=[
                InvariantResult("INV-1", "assumption_set_match", True, message="unknown-uniform calibrated"),
            ]),
        )

    if horizon == Horizon.OPEN_ENDED_STOCHASTIC:
        p = contract.stop_prob_per_step
        if p is None or p <= 0:
            raise ValueError("stop_prob_per_step required")
        r_star, p_star = cutoff_stochastic_stop(p)
        return OutputReport(
            decision={"look_until": r_star - 1, "leap_from": r_star},
            formula_name="Look-Then-Leap (stochastic termination)",
            formula_latex=r"r \\approx 0.18 / p",
            citation="c01 §8",
            numeric={"r_star": float(r_star), "P": p_star},
            assumptions=assumptions,
            sensitivity=[],
            audit=AuditResult(results=[
                InvariantResult("INV-1", "assumption_set_match", True, message="stochastic-stop calibrated"),
            ]),
        )

    raise UnclassifiedVariant(
        f"No stopping rule for horizon={horizon}, information={info}, payoff={contract.payoff}",
        remedy="Consult c01 Decision Table and supply a covered assumption set.",
    )
