"""Engine B golden tests."""

import pytest
from dominant_circuit import (
    dispatch, InputContract, Job, AttributeRange, IndependenceTest,
    IndependenceNotVerified,
)
from dominant_circuit.engines.multiobjective import (
    solve_multiplicative_k, efficient_frontier,
)


def test_multiplicative_k_additive_special_case():
    assert abs(solve_multiplicative_k([0.4, 0.6])) < 1e-10


def test_multiplicative_k_positive():
    k = solve_multiplicative_k([0.3, 0.3])
    assert k > 0


def test_multiplicative_k_negative():
    k = solve_multiplicative_k([0.7, 0.7])
    assert -1 < k < 0


def test_independence_gate():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[
            AttributeRange("salary", 40, 100),
            AttributeRange("commute", 60, 10, monotonic_increasing=False),
        ],
        scaling_constants={"salary": 0.65, "commute": 0.35},
        independence_tests=[],
    )
    with pytest.raises(IndependenceNotVerified):
        dispatch(Job.MULTIOBJECTIVE, contract)


def test_additive_ranking():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[
            AttributeRange("salary", 40, 100),
            AttributeRange("commute", 60, 10, monotonic_increasing=False),
        ],
        scaling_constants={"salary": 0.65, "commute": 0.35},
        independence_tests=[
            IndependenceTest(pair=("salary", "commute"), method="flip_test", passed=True),
            IndependenceTest(pair=("salary", "commute"), method="question_ii", passed=True),
        ],
        alternatives=[
            {"name": "A", "salary": 80, "commute": 20},
            {"name": "B", "salary": 60, "commute": 15},
            {"name": "C", "salary": 90, "commute": 50},
        ],
    )
    report = dispatch(Job.MULTIOBJECTIVE, contract)
    assert report.decision["form"] == "additive"
    assert report.decision["best_alternative"] is not None
    assert report.audit.passed
    assert "c02" in report.citation


def test_dominance():
    attrs = [
        AttributeRange("x", 0, 10),
        AttributeRange("y", 0, 10),
    ]
    alts = [
        {"name": "dom", "x": 5, "y": 5},
        {"name": "better", "x": 8, "y": 8},
        {"name": "mixed", "x": 9, "y": 3},
    ]
    frontier = efficient_frontier(alts, attrs)
    names = {a["name"] for a in frontier}
    assert "dom" not in names
    assert "better" in names
