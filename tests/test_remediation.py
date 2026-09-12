"""Public boundary regressions from the engineering worklist, fixtures A-D."""

from dataclasses import replace
import pytest
from dominant_circuit import (
    InputContract,
    Job,
    Horizon,
    Information,
    Payoff,
    AttributeRange,
    IndependenceAssumption,
    dispatch,
    overturn_test,
    ContractIncomplete,
)


def mdp(**kwargs):
    states, actions = ["start", "gain", "end"], ["take", "wait"]
    return InputContract(
        job=Job.SEQUENTIAL,
        horizon=Horizon.INFINITE_DISCOUNTED,
        gamma=0.9,
        markov_verified=True,
        states=states,
        actions=actions,
        reward={
            (s, a): (
                (1 if a == "take" else 0) if s == "start" else 2 if s == "gain" else 0
            )
            for s in states
            for a in actions
        },
        transition={
            (s, a): {("gain" if a == "wait" else "end") if s == "start" else "end": 1.0}
            for s in states
            for a in actions
        },
        **kwargs,
    )


def stopping(**kwargs):
    return InputContract(
        job=Job.STOPPING,
        horizon=Horizon.FIXED_KNOWN,
        n=100,
        information=Information.ORDINAL,
        payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False,
        **kwargs,
    )


def offers(**kwargs):
    return InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("x", 0, 1), AttributeRange("y", 0, 1)],
        alternatives=[
            {"name": "A", "x": 1.0, "y": 0.0},
            {"name": "B", "x": 0.0, "y": 0.99},
        ],
        scaling_constants={"x": 0.5, "y": 0.5},
        independence_assumptions=[
            IndependenceAssumption(
                frozenset([x]),
                frozenset([y]),
                "preferential",
                True,
                "Synthetic test assumption",
            )
            for x, y in [("x", "y"), ("y", "x")]
        ],
        **kwargs,
    )


def test_fixture_a_budget_is_not_convergence():
    report = dispatch(Job.SEQUENTIAL, mdp(k_max=1))
    assert report.decision["termination_reason"] == "budget_exhausted"
    assert report.decision["final_residual"] == pytest.approx(0.8)
    assert report.decision["last_iterate_difference"] == 2.0
    assert report.decision["recommended_action"] == "wait"
    assert not report.analysis_is_complete
    assert "policy above is optimal" not in report.action
    solved = dispatch(Job.SEQUENTIAL, mdp())
    assert solved.decision["termination_reason"] == "converged"
    assert solved.decision["recommended_action"] == "wait"
    assert solved.decision["value_error_bound"] == 0.0


def test_fixture_b_missing_is_not_false_or_zero():
    with pytest.raises(ContractIncomplete):
        dispatch(Job.STOPPING, stopping())
    assert dispatch(
        Job.STOPPING, stopping(recall_allowed=False, rejection_prob=0.0)
    ).audit.passed


def test_fixture_c_weight_reversal_and_boundary():
    report = dispatch(Job.MULTIOBJECTIVE, offers())
    assert report.decision["winning_margin"] == pytest.approx(0.005)
    changed = dispatch(
        Job.MULTIOBJECTIVE, replace(offers(), scaling_constants={"x": 0.49, "y": 0.51})
    )
    assert changed.decision["best_alternative"] == "B"
    assert report.decision["switching_boundaries"][0]["weight"] == pytest.approx(
        0.99 / 1.99
    )


def test_fixture_d_no_probe_is_untested():
    c = stopping(recall_allowed=False, rejection_prob=0.0)
    result = overturn_test(c, "scores")
    assert result.outcome == "untested"
    assert not result.is_small_quantity
    with pytest.raises(ValueError):
        overturn_test(c, "not_a_field")
