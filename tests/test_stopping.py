"""Golden values from SPEC §14.1–§14.4."""

import math
import pytest
from dominant_circuit import (
    dispatch, InputContract, Job, Horizon, Information, Payoff,
    ContractIncomplete, NoOptimalStoppingRuleExists, UnclassifiedVariant,
)
from dominant_circuit.engines.stopping import (
    optimal_cutoff, asymptotic_cutoff, threshold_percentile,
    cost_aware_threshold, parking_cutoff, parking_cutoff_exact,
    cutoff_with_recall, cutoff_with_rejection,
)


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
