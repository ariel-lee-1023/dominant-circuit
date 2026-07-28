"""Engine A — Optimal Stopping (Cluster 01). Exact finite-n by default."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Optional, Sequence, Tuple

from ..core.contract import InputContract, Horizon, Information, Payoff
from ..core.errors import UnclassifiedVariant, NoOptimalStoppingRuleExists
from ..core.report import OutputReport, AuditResult, InvariantResult, SensitivityEntry


@dataclass(frozen=True)
class Calibration:
    """The assumption set a constant was derived under. c01 §8 / Decision Table."""
    rule: str
    citation: str
    horizon: Optional[Horizon]
    information: Optional[Information]
    payoff: Optional[Payoff]
    recall_allowed: Optional[bool]
    recall_accept_prob: Optional[float]   # None = not applicable
    rejection_prob: Optional[float]
    constant: Optional[float]             # 0.37 / 0.58 / 0.61 / 0.25 / ... ; None if exact


# One entry per row of c01's Decision Table ("Which Rule Applies"), transcribed.
# `constant` is the calibrated figure in the table's final Success-rate column;
# it is None where that column reads "scenario-dependent" or "undefined", i.e.
# where nothing is reused and the quantity is computed exactly from inputs.
# A field set to None is NOT pinned by that row and matches any elicited value.
CALIBRATIONS: dict[str, Calibration] = {
    # Ordinal | Fixed known n | No recall | No rejection | Best-or-nothing
    "classical_37": Calibration(
        rule="Look-Then-Leap (37% Rule)",
        citation="c01 §5",
        horizon=Horizon.FIXED_KNOWN,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=False,
        recall_accept_prob=None,
        rejection_prob=0.0,
        constant=0.37,
    ),
    # Cardinal | Fixed known n | No recall | No rejection | Best-or-nothing
    "threshold_rule_58": Calibration(
        rule="Threshold Rule",
        citation="c01 §6",
        horizon=Horizon.FIXED_KNOWN,
        information=Information.CARDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=False,
        recall_accept_prob=None,
        rejection_prob=0.0,
        constant=0.58,
    ),
    # Ordinal | Fixed known n | Recall @ 50% recall-accept | No rejection
    "recall_61": Calibration(
        rule="Look-Then-Leap + fallback recall",
        citation="c01 §7",
        horizon=Horizon.FIXED_KNOWN,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=True,
        recall_accept_prob=0.5,
        rejection_prob=0.0,
        constant=0.61,
    ),
    # Ordinal | Fixed known n | No recall | Rejection @ 50% accept
    "rejection_25": Calibration(
        rule="Early-and-often proposing",
        citation="c01 §7",
        horizon=Horizon.FIXED_KNOWN,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=False,
        recall_accept_prob=None,
        rejection_prob=0.5,
        constant=0.25,
    ),
    # Ordinal | Unknown n ~ Uniform[1, n_max] | No recall | No rejection
    "unknown_n_uniform_27": Calibration(
        rule="Look-Then-Leap (unknown n ~ Uniform)",
        citation="c01 §8",
        horizon=Horizon.FIXED_UNKNOWN_UNIFORM,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=False,
        recall_accept_prob=None,
        rejection_prob=0.0,
        constant=2.0 / (math.e ** 2),
    ),
    # Ordinal | Open-ended, stops w.p. p per step | No recall | No rejection
    "stochastic_stop_236": Calibration(
        rule="Look-Then-Leap (stochastic termination)",
        citation="c01 §8",
        horizon=Horizon.OPEN_ENDED_STOCHASTIC,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=False,
        recall_accept_prob=None,
        rejection_prob=0.0,
        constant=0.236,
    ),
    # Cardinal | Unbounded stream, per-offer cost c | Recall never optimal
    "cost_aware_threshold": Calibration(
        rule="Cost-Aware Threshold",
        citation="c01 §9",
        horizon=None,                       # table: "Unbounded stream"
        information=Information.CARDINAL,
        payoff=Payoff.COST_OF_SEARCH,
        recall_allowed=False,               # table: "Never optimal"
        recall_accept_prob=None,
        rejection_prob=None,                # table: N/A
        constant=None,                      # exact: p* solves (1-p)^2/2 = c
    ),
    # Ordinal/positional | Unbounded spatial sequence, occupancy p
    "parking_threshold": Calibration(
        rule="Parking Threshold",
        citation="c01 §10",
        horizon=None,                       # table: "Unbounded spatial sequence"
        information=None,                   # table: "Ordinal/positional" (a disjunction)
        payoff=Payoff.DURATION,             # table: "Minimize distance"
        recall_allowed=False,
        recall_accept_prob=None,
        rejection_prob=0.0,
        constant=None,                      # exact: floor(-log 2 / log p)
    ),
    # N/A | Repeated trials, ruin on failure | Accumulate then stop
    "burglar_rule": Calibration(
        rule="Burglar Rule",
        citation="c01 §11",
        horizon=None,
        information=None,
        payoff=Payoff.RUIN_RISK,
        recall_allowed=None,
        recall_accept_prob=None,
        rejection_prob=None,
        constant=None,                      # exact: ceiling = mq/(1-q)
    ),
    # N/A | Any | Reward diverges at the best stopping point -> no rule exists
    "no_rule_exists": Calibration(
        rule="No rule exists",
        citation="c01 §8",
        horizon=None,
        information=None,
        payoff=None,
        recall_allowed=None,
        recall_accept_prob=None,
        rejection_prob=None,
        constant=None,
    ),
}

# Fields compared by INV-1, in report order.
_PINNED_FIELDS = (
    "horizon", "information", "payoff",
    "recall_allowed", "recall_accept_prob", "rejection_prob",
)

# How solve_stopping's own branch logic reads an unelicited value. INV-1 compares
# against the same normalization so it flags real contradictions, not silence.
_CONTRACT_DEFAULTS = {"recall_allowed": False, "rejection_prob": 0.0}


def _elicited(contract: InputContract, field_name: str) -> Any:
    value = getattr(contract, field_name)
    if value is None and field_name in _CONTRACT_DEFAULTS:
        return _CONTRACT_DEFAULTS[field_name]
    return value


def _values_match(pinned: Any, elicited: Any) -> bool:
    if isinstance(pinned, float) and isinstance(elicited, (int, float)) and not isinstance(elicited, bool):
        return abs(float(elicited) - pinned) <= 1e-9
    return pinned == elicited


def _tuple_repr(source: Any, getter) -> str:
    parts = []
    for name in _PINNED_FIELDS:
        value = getter(source, name)
        parts.append(f"{name}={getattr(value, 'value', value)!r}")
    return "(" + ", ".join(parts) + ")"


def check_assumption_set_match(contract: InputContract,
                               calibration: Calibration) -> InvariantResult:
    """INV-1. Compare the elicited assumption tuple against the calibration record
    of the constant actually dispatched. Any mismatch on a field the calibration
    pins is a FAILURE, with both tuples in the message."""
    mismatches: list[str] = []
    for name in _PINNED_FIELDS:
        pinned = getattr(calibration, name)
        if pinned is None:
            continue                                  # not pinned by this rule
        got = _elicited(contract, name)
        if not _values_match(pinned, got):
            mismatches.append(
                f"{name}: calibrated for {getattr(pinned, 'value', pinned)!r}, "
                f"elicited {getattr(got, 'value', got)!r}"
            )

    calibrated_tuple = _tuple_repr(calibration, lambda c, n: getattr(c, n))
    elicited_tuple = _tuple_repr(contract, _elicited)
    constant_note = (
        "no constant reused (computed exactly)" if calibration.constant is None
        else f"constant {calibration.constant:.4g} reused"
    )

    passed = not mismatches
    if passed:
        message = (
            f"'{calibration.rule}' ({calibration.citation}) matches the elicited "
            f"assumption set {elicited_tuple} [{constant_note}]"
        )
    else:
        message = (
            f"'{calibration.rule}' ({calibration.citation}) is not calibrated for the "
            f"elicited assumption set. Mismatches: {'; '.join(mismatches)}. "
            f"calibration={calibrated_tuple} elicited={elicited_tuple} [{constant_note}]"
        )

    return InvariantResult("INV-1", "assumption_set_match", passed, message=message)


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

    # --- Silent-precedence guards -------------------------------------------------
    # Each of these assumption combinations previously fell through to whichever
    # branch happened to be tested first, silently returning a constant calibrated
    # for a different problem. No row of c01's Decision Table covers them.

    recall_active = bool(contract.recall_allowed) and contract.recall_accept_prob is not None
    rejection_active = contract.rejection_prob is not None and contract.rejection_prob > 0
    if recall_active and rejection_active:
        raise UnclassifiedVariant(
            "c01's Decision Table has no row for simultaneous recall and rejection risk. "
            "The two move the look/leap boundary in opposite directions (c01 §7 Invariant) "
            "and their combination is not calibrated in the corpus.",
            remedy="Set rejection_prob=0 (or recall_allowed=False), or supply a source "
                   "that calibrates the joint case.",
            field="recall_allowed",
        )

    # c01 §9 applies only under full information ("Applies when: full information
    # exists"); Decision Table row 7 pins Cardinal. Ordinal + cost-of-search is
    # uncalibrated, and previously took the cost-aware branch regardless.
    if contract.payoff == Payoff.COST_OF_SEARCH and contract.information == Information.ORDINAL:
        raise UnclassifiedVariant(
            "The Cost-Aware Threshold (c01 §9) is derived under full cardinal information; "
            "c01 has no cost-of-search row for ordinal-only information.",
            remedy="Supply cardinal scores (information=CARDINAL), or restate the payoff "
                   "as best-or-nothing.",
            field="information",
        )

    # Decision Table row 2 (Threshold Rule) pins a fixed, known n. The cardinal
    # branch is tested before the horizon branches, so any other horizon silently
    # received the 0.58-calibrated Threshold Rule.
    if (contract.information == Information.CARDINAL
            and contract.payoff != Payoff.COST_OF_SEARCH
            and contract.horizon is not None
            and contract.horizon != Horizon.FIXED_KNOWN):
        raise UnclassifiedVariant(
            f"c01 has no cardinal-information row for horizon={contract.horizon.value}. "
            "The Threshold Rule (c01 §6) is calibrated for a fixed, known n; the "
            "unknown-n and stochastic-termination rows are ordinal-only.",
            remedy="Supply a fixed, known n, or restate the problem as ordinal-only.",
            field="horizon",
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
        "ruin_success_prob": contract.ruin_success_prob,
        "ruin_mean_gain": contract.ruin_mean_gain,
    }

    if contract.payoff == Payoff.COST_OF_SEARCH:
        if contract.search_cost is None:
            raise ValueError("search_cost required for COST_OF_SEARCH")
        thr = cost_aware_threshold(0.0, 1.0, contract.search_cost)
        cal = CALIBRATIONS["cost_aware_threshold"]
        return OutputReport(
            decision=thr,
            formula_name=cal.rule,
            formula_latex=r"p^* = 1 - \sqrt{2c}",
            citation=cal.citation,
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
                check_assumption_set_match(contract, cal),
                InvariantResult("INV-6", "finite_expectation", True, message="cost-of-search has finite expectation"),
            ]),
        )

    if contract.payoff == Payoff.RUIN_RISK:
        q, m = contract.ruin_success_prob, contract.ruin_mean_gain
        if q is None or m is None:
            raise ValueError("ruin_success_prob (q) and ruin_mean_gain (m) required for RUIN_RISK")
        ceiling = burglar_ceiling(q, m)
        expected_trials = q / (1.0 - q)
        cal = CALIBRATIONS["burglar_rule"]
        return OutputReport(
            decision={"stop_when_accumulated_at_least": ceiling},
            formula_name=cal.rule,
            formula_latex=r"\text{ceiling} = \frac{mq}{1-q}",
            citation=cal.citation,
            numeric={
                "ceiling": ceiling,
                "q": q,
                "m": m,
                "expected_trials_before_stopping": expected_trials,
            },
            assumptions=assumptions,
            sensitivity=[
                SensitivityEntry(
                    assumption="ruin_success_prob",
                    perturbation=f"q={q} → higher (closer to 1)",
                    new_decision="ceiling rises without bound as q → 1",
                    decision_changed=True,
                    fragility="critical",
                ),
            ],
            audit=AuditResult(results=[
                check_assumption_set_match(contract, cal),
                InvariantResult(
                    "INV-6", "finite_expectation", True,
                    message="ruin-risk accumulation has a finite ceiling mq/(1-q)",
                ),
            ]),
        )

    info = contract.information
    horizon = contract.horizon
    n = contract.n

    if info == Information.CARDINAL:
        cal = CALIBRATIONS["threshold_rule_58"]
        schedule = {k: threshold_percentile(k) for k in range(0, 11)}
        return OutputReport(
            decision="threshold_schedule",
            formula_name=cal.rule,
            formula_latex=r"t_k = 1/(1 + 0.804/k + 0.183/k^2)",
            citation=cal.citation,
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
                check_assumption_set_match(contract, cal),
            ]),
        )

    if horizon == Horizon.FIXED_KNOWN:
        if n is None or n < 1:
            raise ValueError("n required for FIXED_KNOWN")
        if contract.recall_allowed and contract.recall_accept_prob is not None:
            r_star, p_star = cutoff_with_recall(n, contract.recall_accept_prob)
            cal = CALIBRATIONS["recall_61"]
            latex = r"r \approx 0.61 n \quad (50\%\ \mathrm{recall\text{-}accept})"
        elif contract.rejection_prob is not None and contract.rejection_prob > 0:
            r_star, p_star = cutoff_with_rejection(n, contract.rejection_prob)
            cal = CALIBRATIONS["rejection_25"]
            latex = r"r \approx 0.25 n \quad (50\%\ \mathrm{accept})"
        else:
            if contract.exact_finite_n:
                r_star, p_star = optimal_cutoff(n)
                # Row 1's assumption set, but computed exactly: no constant is reused,
                # so `constant` is None and the citation is the finite-n argmax.
                cal = replace(
                    CALIBRATIONS["classical_37"],
                    rule="Look-Then-Leap (exact finite-n)",
                    citation="c01 §4.1",
                    constant=None,
                )
                latex = r"r^* = \arg\max_r P_n(r),\quad P_n(r)=\frac{r-1}{n}\sum_{j=r}^{n}\frac{1}{j-1}"
            else:
                r_star, p_star = asymptotic_cutoff(n)
                cal = replace(
                    CALIBRATIONS["classical_37"],
                    rule="Look-Then-Leap (asymptotic 1/e)",
                )
                latex = r"r \approx n/e,\quad P\to 1/e"

        formula = cal.rule
        cite = cal.citation

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
                check_assumption_set_match(contract, cal),
                InvariantResult("INV-6", "finite_expectation", True, message="best-or-nothing has finite expectation"),
            ]),
        )

    if horizon == Horizon.FIXED_UNKNOWN_UNIFORM:
        n_max = contract.n_max or n
        if n_max is None:
            raise ValueError("n_max required")
        r_star, p_star = cutoff_unknown_horizon_uniform(n_max)
        cal = CALIBRATIONS["unknown_n_uniform_27"]
        return OutputReport(
            decision={"look_until": r_star - 1, "leap_from": r_star},
            formula_name=cal.rule,
            formula_latex=r"r \approx n_{\max}/e^2",
            citation=cal.citation,
            numeric={"r_star": float(r_star), "P": p_star},
            assumptions=assumptions,
            sensitivity=[],
            audit=AuditResult(results=[
                check_assumption_set_match(contract, cal),
            ]),
        )

    if horizon == Horizon.OPEN_ENDED_STOCHASTIC:
        p = contract.stop_prob_per_step
        if p is None or p <= 0:
            raise ValueError("stop_prob_per_step required")
        r_star, p_star = cutoff_stochastic_stop(p)
        cal = CALIBRATIONS["stochastic_stop_236"]
        return OutputReport(
            decision={"look_until": r_star - 1, "leap_from": r_star},
            formula_name=cal.rule,
            formula_latex=r"r \approx 0.18 / p",
            citation=cal.citation,
            numeric={"r_star": float(r_star), "P": p_star},
            assumptions=assumptions,
            sensitivity=[],
            audit=AuditResult(results=[
                check_assumption_set_match(contract, cal),
            ]),
        )

    raise UnclassifiedVariant(
        f"No stopping rule for horizon={horizon}, information={info}, payoff={contract.payoff}",
        remedy="Consult c01 Decision Table and supply a covered assumption set.",
    )
