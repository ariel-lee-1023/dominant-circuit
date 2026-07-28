"""Stage 4 (validation invariants) and the Output Contract's rendering.

These two modules carry the audit result the whole product rests on, and were
the least exercised paths in the suite.
"""

import math

import pytest

from dominant_circuit import (
    AttributeRange, AuditFailure, AuditResult, Horizon, Information,
    IndependenceAssumption, InputContract, InvariantResult, Job, OutputReport,
    Payoff, RiskAttitude, SensitivityEntry, check_range_fixed_weights,
    dispatch, run_validation_invariants,
)
from dominant_circuit.core.audit import require_audit_pass
from dominant_circuit.engines.stopping import CALIBRATIONS


def _attrs():
    return [AttributeRange("a", 0, 10), AttributeRange("b", 0, 10)]


def _registry(names=("a", "b"), kind="preferential", verified=True):
    all_attrs = frozenset(names)
    return [
        IndependenceAssumption(subset=frozenset({n}), complement=all_attrs - {n},
                               kind=kind, verified=verified)
        for n in names
    ]


# --- INV-5: range-fixed weights ---------------------------------------------------

def test_inv5_flags_weight_without_range():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 0, 10)],
        scaling_constants={"a": 0.5, "ghost": 0.5},
    )
    result = check_range_fixed_weights(contract)
    assert result.passed is False
    assert "ghost" in result.message


def test_inv5_flags_degenerate_range():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 5, 5)],       # worst == best
        scaling_constants={"a": 1.0},
    )
    result = check_range_fixed_weights(contract)
    assert result.passed is False
    assert "degenerate" in result.message


def test_inv5_passes_when_every_weight_has_a_real_range():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE, attributes=_attrs(),
        scaling_constants={"a": 0.4, "b": 0.6},
    )
    assert check_range_fixed_weights(contract).passed


# --- run_validation_invariants ----------------------------------------------------

def test_inv2_belief_normalization():
    contract = InputContract(job=Job.SEQUENTIAL, gamma=0.9)
    ok = run_validation_invariants(Job.SEQUENTIAL, contract, None,
                                   {"belief": {"s1": 0.5, "s2": 0.5}})
    inv2 = next(r for r in ok.results if r.invariant_id == "INV-2")
    assert inv2.passed

    bad = run_validation_invariants(Job.SEQUENTIAL, contract, None,
                                    {"belief": {"s1": 0.5, "s2": 0.9}})
    inv2 = next(r for r in bad.results if r.invariant_id == "INV-2")
    assert not inv2.passed
    assert inv2.residual == pytest.approx(0.4)


def test_inv4_bellman_residual_monotonicity():
    contract = InputContract(job=Job.SEQUENTIAL, gamma=0.5)
    shrinking = run_validation_invariants(
        Job.SEQUENTIAL, contract, None, {"residual_history": [1.0, 0.4, 0.15]})
    inv4 = next(r for r in shrinking.results if r.invariant_id == "INV-4")
    assert inv4.passed

    growing = run_validation_invariants(
        Job.SEQUENTIAL, contract, None, {"residual_history": [1.0, 2.0, 3.0]})
    inv4 = next(r for r in growing.results if r.invariant_id == "INV-4")
    assert not inv4.passed


def test_inv6_finite_expectation():
    diverging = InputContract(job=Job.STOPPING, payoff_diverges=True)
    audit = run_validation_invariants(Job.STOPPING, diverging, None)
    inv6 = next(r for r in audit.results if r.invariant_id == "INV-6")
    assert not inv6.passed


def test_inv7_overdetermination():
    contract = InputContract(job=Job.STOPPING, payoff_diverges=False)
    under = run_validation_invariants(Job.STOPPING, contract, None,
                                      {"n_tradeoff_equations": 2, "n_free_parameters": 3})
    inv7 = next(r for r in under.results if r.invariant_id == "INV-7")
    assert not inv7.passed

    over = run_validation_invariants(Job.STOPPING, contract, None,
                                     {"n_tradeoff_equations": 5, "n_free_parameters": 3})
    inv7 = next(r for r in over.results if r.invariant_id == "INV-7")
    assert inv7.passed


def test_inv1_emitted_only_when_a_calibration_is_supplied():
    """run_validation_invariants does not know which rule was dispatched, so it
    must not invent an INV-1 result."""
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False,
    )
    without = run_validation_invariants(Job.STOPPING, contract, None)
    assert not any(r.invariant_id == "INV-1" for r in without.results)

    with_cal = run_validation_invariants(
        Job.STOPPING, contract, None, {"calibration": CALIBRATIONS["classical_37"]})
    inv1 = next(r for r in with_cal.results if r.invariant_id == "INV-1")
    assert inv1.passed


def test_inv3_via_run_validation_invariants():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE, attributes=_attrs(),
        scaling_constants={"a": 0.4, "b": 0.6},
        independence_assumptions=_registry(),
    )
    audit = run_validation_invariants(Job.MULTIOBJECTIVE, contract, None)
    inv3 = next(r for r in audit.results if r.invariant_id == "INV-3")
    assert inv3.passed

    contract.independence_assumptions = []
    audit = run_validation_invariants(Job.MULTIOBJECTIVE, contract, None)
    inv3 = next(r for r in audit.results if r.invariant_id == "INV-3")
    assert not inv3.passed


# --- require_audit_pass -----------------------------------------------------------

def test_require_audit_pass_names_the_failed_invariants():
    audit = AuditResult(results=[
        InvariantResult("INV-1", "assumption_set_match", False, message="x"),
        InvariantResult("INV-6", "finite_expectation", False, message="y"),
        InvariantResult("INV-2", "belief_normalization", True, message="z"),
    ])
    with pytest.raises(AuditFailure) as ei:
        require_audit_pass(audit)
    assert "INV-1" in str(ei.value) and "INV-6" in str(ei.value)
    assert "INV-2" not in str(ei.value)


def test_require_audit_pass_is_silent_when_clean():
    require_audit_pass(AuditResult(results=[
        InvariantResult("INV-1", "assumption_set_match", True),
    ]))


def test_audit_result_properties():
    passing = InvariantResult("INV-1", "a", True)
    failing = InvariantResult("INV-2", "b", False)
    audit = AuditResult(results=[passing, failing])
    assert audit.passed is False
    assert audit.failures == [failing]
    assert AuditResult(results=[passing]).passed is True
    assert AuditResult().passed is True          # vacuous


# --- OutputReport rendering -------------------------------------------------------

def _report(audit=None):
    return OutputReport(
        decision={"look_until": 37, "leap_from": 38},
        formula_name="Look-Then-Leap (exact finite-n)",
        formula_latex=r"r^* = \arg\max_r P_n(r)",
        citation="c01 §4.1",
        numeric={"r_star": 38.0, "P_n": 0.371043},
        assumptions={"horizon": "fixed_known", "n": 100},
        sensitivity=[SensitivityEntry("exact_finite_n", "True → False", 37, True, "fragile")],
        audit=audit or AuditResult(results=[
            InvariantResult("INV-1", "assumption_set_match", True, message="matches"),
        ]),
    )


def test_to_markdown_carries_all_six_output_contract_fields():
    md = _report().to_markdown()
    for heading in ("## Decision", "## Formula", "## Numeric",
                    "## Assumptions", "## Sensitivity", "## Audit"):
        assert heading in md, heading
    assert "c01 §4.1" in md
    assert "r_star: 38.0" in md
    assert "Status: **PASS**" in md
    assert "[✓] INV-1" in md


def test_to_markdown_marks_a_failed_audit():
    failing = AuditResult(results=[
        InvariantResult("INV-1", "assumption_set_match", False, message="mismatch"),
    ])
    md = _report(failing).to_markdown()
    assert "Status: **FAIL**" in md
    assert "[✗] INV-1" in md
    assert "mismatch" in md


def test_to_markdown_renders_latex_with_single_backslashes():
    """T8.1: reports must not show literal double backslashes."""
    md = _report().to_markdown()
    assert r"\arg\max" in md
    assert r"\\arg" not in md


def test_every_dispatched_report_renders_single_backslash_latex():
    contracts = [
        InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=50,
                      information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
                      payoff_diverges=False),
        InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=50,
                      information=Information.CARDINAL, payoff=Payoff.BEST_OR_NOTHING,
                      payoff_diverges=False),
        InputContract(job=Job.STOPPING, horizon=Horizon.UNBOUNDED_STREAM,
                      information=Information.CARDINAL, payoff=Payoff.COST_OF_SEARCH,
                      search_cost=0.02, payoff_diverges=False),
        InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_UNKNOWN_UNIFORM,
                      n_max=100, information=Information.ORDINAL,
                      payoff=Payoff.BEST_OR_NOTHING, payoff_diverges=False),
        InputContract(job=Job.STOPPING, horizon=Horizon.OPEN_ENDED_STOCHASTIC,
                      stop_prob_per_step=0.01, information=Information.ORDINAL,
                      payoff=Payoff.BEST_OR_NOTHING, payoff_diverges=False),
    ]
    for contract in contracts:
        report = dispatch(Job.STOPPING, contract)
        assert "\\\\" not in report.formula_latex, report.formula_name
        assert "\\\\" not in report.to_markdown(), report.formula_name


def test_to_dict_round_trips():
    d = _report().to_dict()
    assert d["citation"] == "c01 §4.1"
    assert d["audit"]["results"][0]["invariant_id"] == "INV-1"
    assert d["sensitivity"][0]["fragility"] == "fragile"


# --- uncertainty vs certainty kind ------------------------------------------------

def test_risk_attitude_switches_independence_kind():
    certainty = InputContract(job=Job.MULTIOBJECTIVE, attributes=_attrs())
    assert certainty.independence_kind == "preferential"
    assert certainty.job_is_under_uncertainty is False

    uncertainty = InputContract(job=Job.MULTIOBJECTIVE, attributes=_attrs(),
                                risk_attitude=RiskAttitude.AVERSE)
    assert uncertainty.independence_kind == "utility"
    assert uncertainty.job_is_under_uncertainty is True


def test_utility_kind_registry_is_not_accepted_for_a_certainty_problem():
    """A registry recorded as 'utility' does not satisfy a preferential gate."""
    from dominant_circuit import mutual_independence_holds
    reg = _registry(kind="utility")
    assert mutual_independence_holds(reg, frozenset({"a", "b"}), "utility")
    assert not mutual_independence_holds(reg, frozenset({"a", "b"}), "preferential")
