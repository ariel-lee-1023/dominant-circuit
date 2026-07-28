"""Golden values from SPEC §14.1–§14.4."""

import math
from pathlib import Path

import pytest
from dominant_circuit import (
    dispatch, InputContract, Job, Horizon, Information, Payoff,
    ContractIncomplete, NoOptimalStoppingRuleExists, UnclassifiedVariant,
)
from dominant_circuit.engines.stopping import (
    optimal_cutoff, asymptotic_cutoff, threshold_percentile,
    cost_aware_threshold, parking_cutoff, parking_cutoff_exact,
    cutoff_with_recall, cutoff_with_rejection,
    CALIBRATIONS, Calibration, check_assumption_set_match,
    threshold_rule, threshold_schedule,
)

SRC = Path(__file__).resolve().parents[1] / "src" / "dominant_circuit"


def test_exact_finite_n_table():
    expected = {
        1: (1, 1.0),
        2: (1, 0.5),
        3: (2, 0.5),
        4: (2, 0.458333),
        5: (3, 0.433333),
        10: (4, 0.398690),
        100: (38, 0.371043),
        1000: (369, 0.368196),
    }
    for n, (r_exp, p_exp) in expected.items():
        r, p = optimal_cutoff(n)
        assert r == r_exp, f"n={n}: r*={r} expected {r_exp}"
        assert abs(p - p_exp) < 1e-5, f"n={n}: P={p} expected {p_exp}"


def test_exact_beats_asymptotic_at_n100():
    assert optimal_cutoff(100)[0] == 38
    assert asymptotic_cutoff(100)[0] == 37
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False, exact_finite_n=True,
    )
    report = dispatch(Job.STOPPING, contract)
    assert report.numeric["r_star"] == 38


def test_threshold_percentiles():
    expected = {1: 0.5033, 2: 0.6907, 3: 0.7762, 4: 0.8248, 10: 0.9240, 50: 0.9841}
    for k, t_exp in expected.items():
        assert abs(threshold_percentile(k) - t_exp) < 1e-3


def test_recall_constant_locked():
    assert cutoff_with_recall(100, 0.5)[0] == 61
    with pytest.raises(UnclassifiedVariant):
        cutoff_with_recall(100, 0.3)


def test_rejection_constant_locked():
    assert cutoff_with_rejection(100, 0.5)[0] == 25
    with pytest.raises(UnclassifiedVariant):
        cutoff_with_rejection(100, 0.2)


def test_cost_aware():
    assert abs(cost_aware_threshold(0, 1, 0.02) - 0.8) < 1e-6
    assert abs(cost_aware_threshold(0, 1, 0.5)) < 1e-9
    assert abs(cost_aware_threshold(100000, 200000, 0.02) - 180000) < 1e-6


def test_parking_corrected():
    assert parking_cutoff(0.90) == 6
    assert parking_cutoff(0.95) == 13
    assert parking_cutoff(0.99) == 68
    ps = [0.5, 0.85, 0.9, 0.95, 0.99]
    ds = [parking_cutoff(p) for p in ps]
    assert ds == sorted(ds)
    assert all(d > 0 for d in ds)
    ratio = parking_cutoff_exact(0.95) / parking_cutoff_exact(0.90)
    assert abs(ratio - 2.0) < 0.15


def test_diverging_blocks():
    c = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=10,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=True,
    )
    with pytest.raises(NoOptimalStoppingRuleExists) as ei:
        dispatch(Job.STOPPING, c)
    assert "Kelly" in ei.value.remedy


def test_unelicited_divergence_not_assumed_false():
    c = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=10,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=None,
    )
    with pytest.raises(ContractIncomplete) as ei:
        dispatch(Job.STOPPING, c)
    assert ei.value.field == "payoff_diverges"


def _contract_with(**overrides):
    base = dict(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False,
    )
    base.update(overrides)
    return InputContract(**base)


def test_recall_and_rejection_both_set_raises():
    """c01 has no Decision Table row for simultaneous recall and rejection risk."""
    with pytest.raises(UnclassifiedVariant) as ei:
        dispatch(Job.STOPPING, _contract_with(recall_allowed=True,
                 recall_accept_prob=0.5, rejection_prob=0.5))
    assert "c01 §7" in str(ei.value)
    assert ei.value.remedy


def test_recall_alone_still_dispatches():
    report = dispatch(Job.STOPPING, _contract_with(recall_allowed=True, recall_accept_prob=0.5))
    assert report.numeric["r_star"] == 61
    assert report.audit.passed


def test_rejection_alone_still_dispatches():
    report = dispatch(Job.STOPPING, _contract_with(rejection_prob=0.5))
    assert report.numeric["r_star"] == 25
    assert report.audit.passed


def test_cost_of_search_with_ordinal_information_raises():
    """c01 §9 is derived under full cardinal information."""
    with pytest.raises(UnclassifiedVariant):
        dispatch(Job.STOPPING, _contract_with(
            payoff=Payoff.COST_OF_SEARCH, search_cost=0.02,
            information=Information.ORDINAL,
        ))


def test_cardinal_with_non_fixed_horizon_raises():
    """The Threshold Rule's 58% is pinned to Decision Table row 2 (fixed, known n)."""
    with pytest.raises(UnclassifiedVariant):
        dispatch(Job.STOPPING, _contract_with(
            horizon=Horizon.OPEN_ENDED_STOCHASTIC, stop_prob_per_step=0.01,
            information=Information.CARDINAL,
        ))


def test_ruin_risk_returns_burglar_ceiling():
    report = dispatch(Job.STOPPING, _contract_with(
        payoff=Payoff.RUIN_RISK, ruin_success_prob=0.9, ruin_mean_gain=1.0,
    ))
    assert abs(report.numeric["ceiling"] - 9.0) < 1e-9
    assert report.citation == "c01 §11"
    assert report.audit.passed


def test_ruin_risk_requires_q_and_m():
    for missing in ("ruin_success_prob", "ruin_mean_gain"):
        kwargs = {"payoff": Payoff.RUIN_RISK, "ruin_success_prob": 0.9, "ruin_mean_gain": 1.0}
        kwargs[missing] = None
        with pytest.raises(ContractIncomplete) as ei:
            dispatch(Job.STOPPING, _contract_with(**kwargs))
        assert ei.value.field == missing


def test_calibration_registry_covers_the_decision_table():
    """c01's Decision Table has ten rows; the registry transcribes all ten."""
    assert len(CALIBRATIONS) == 10
    for key, cal in CALIBRATIONS.items():
        assert isinstance(cal, Calibration), key
        assert cal.citation.startswith("c01 §"), key
        assert cal.rule, key


def test_inv1_fails_on_mismatched_calibration():
    """Hand a rule its calibration record and a contract that contradicts it."""
    # The 0.61 recall constant, handed a contract that elicited no recall at all.
    cal = CALIBRATIONS["recall_61"]
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False, recall_allowed=False,
    )
    result = check_assumption_set_match(contract, cal)

    assert result.passed is False
    assert result.invariant_id == "INV-1"
    # both tuples must be in the message, so the report is self-explanatory
    assert "calibration=" in result.message
    assert "elicited=" in result.message
    assert "recall_allowed" in result.message


def test_inv1_passes_on_matching_calibration():
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False,
    )
    assert check_assumption_set_match(contract, CALIBRATIONS["classical_37"]).passed


def test_inv1_none_field_is_not_pinned():
    """A calibration field of None matches anything (c01 Decision Table 'N/A')."""
    cal = CALIBRATIONS["burglar_rule"]
    assert cal.horizon is None and cal.information is None
    for horizon in (Horizon.FIXED_KNOWN, Horizon.UNBOUNDED_STREAM):
        contract = InputContract(job=Job.STOPPING, horizon=horizon, payoff=Payoff.RUIN_RISK)
        assert check_assumption_set_match(contract, cal).passed


def test_inv1_exact_path_reuses_no_constant():
    """constant=None (the exact finite-n path) always passes the constant check."""
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False, exact_finite_n=True,
    )
    report = dispatch(Job.STOPPING, contract)
    inv1 = next(r for r in report.audit.results if r.invariant_id == "INV-1")
    assert inv1.passed
    assert "no constant reused" in inv1.message
    assert report.citation == "c01 §4.1"


def test_inv1_is_not_hardcoded_true():
    """Statically assert no InvariantResult('INV-1', ..., True) literal remains."""
    for f in SRC.rglob("*.py"):
        text = f.read_text()
        assert 'InvariantResult("INV-1"' not in text or "check_assumption_set_match" in text, f


def test_inv5_is_not_hardcoded_true():
    for f in SRC.rglob("*.py"):
        text = f.read_text()
        assert 'InvariantResult("INV-5"' not in text or "check_range_fixed_weights" in text, f


def test_report_has_six_fields():
    c = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=50,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False, exact_finite_n=True,
    )
    r = dispatch(Job.STOPPING, c)
    for f in ("decision", "formula_name", "numeric", "assumptions", "sensitivity", "audit"):
        assert getattr(r, f) is not None
    assert "§" in r.citation
    assert r.audit.passed


# --- T8 small correctness items ---------------------------------------------------

def test_negative_search_cost_raises():
    """c = -5.0 previously clamped to 0 and returned 1.0, the TOP of the range."""
    with pytest.raises(ValueError):
        cost_aware_threshold(0.0, 1.0, -5.0)
    with pytest.raises(ValueError):
        cost_aware_threshold(0.0, 1.0, -1e-9)


def test_search_cost_upper_clamp_retained():
    """c01 §9: a cost at or above half the range collapses to the bottom."""
    assert cost_aware_threshold(0.0, 1.0, 0.5) == pytest.approx(0.0)
    assert cost_aware_threshold(0.0, 1.0, 5.0) == pytest.approx(0.0)
    assert cost_aware_threshold(10.0, 20.0, 0.5) == pytest.approx(10.0)


def test_threshold_schedule_uses_actual_n():
    """The cardinal branch built a hardcoded 0..10 schedule regardless of n."""
    sched = threshold_schedule(5)
    assert set(sched) == {1, 2, 3, 4, 5}
    assert sched[5] == 0.0                       # last candidate: accept unconditionally
    assert sched[4] == pytest.approx(threshold_percentile(1))
    # earlier positions are strictly more selective
    assert sched[1] > sched[2] > sched[3] > sched[4] > sched[5]


def test_threshold_rule_returns_accepted_index():
    n = 5
    sched = threshold_schedule(n)
    # a candidate at position 2 that clears its threshold is accepted there
    scores = [0.0, min(1.0, sched[2] + 1e-9), 0.0, 0.0, 0.0]
    assert threshold_rule(n, scores) == 2
    # nobody clears -> forced acceptance of the last
    assert threshold_rule(n, [0.0] * n) == n
    # no scores -> the schedule itself
    assert threshold_rule(n) == sched
    with pytest.raises(ValueError):
        threshold_rule(n, [0.0] * (n - 1))


def test_cardinal_dispatch_uses_n():
    c = _contract_with(information=Information.CARDINAL, n=7)
    report = dispatch(Job.STOPPING, c)
    assert report.decision["n"] == 7
    assert set(report.decision["schedule"]) == set(range(1, 8))
    assert report.citation == "c01 §6"
    assert report.audit.passed


def test_cardinal_dispatch_with_scores_returns_index():
    n = 6
    sched = threshold_schedule(n)
    scores = [0.0, 0.0, min(1.0, sched[3] + 1e-9), 0.0, 0.0, 0.0]
    report = dispatch(Job.STOPPING, _contract_with(
        information=Information.CARDINAL, n=n, scores=scores))
    assert report.decision["accept_at"] == 3
