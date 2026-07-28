"""Engine B golden tests."""

import pytest
from dominant_circuit import (
    dispatch, InputContract, Job, AttributeRange, IndependenceTest,
    IndependenceAssumption, IndependenceNotVerified, ContractIncomplete,
)
from dominant_circuit.engines.multiobjective import (
    solve_multiplicative_k, efficient_frontier, run_flip_test,
    mutual_independence_holds, uncovered_independence_subsets,
    check_independence_and_form, required_independence_subsets,
)


def _mutually_independent(names, kind="preferential"):
    """Build a registry that covers every proper nonempty subset."""
    all_attrs = frozenset(names)
    return [
        IndependenceAssumption(
            subset=s, complement=all_attrs - s, kind=kind,
            verified=True, evidence="test fixture",
        )
        for s in required_independence_subsets(all_attrs)
    ]


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


def test_partial_coverage_rejected():
    """3 attributes, only one pair recorded -> IndependenceNotVerified naming the gaps."""
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[
            AttributeRange("salary", 40, 100),
            AttributeRange("commute", 60, 10, monotonic_increasing=False),
            AttributeRange("prestige", 0, 10),
        ],
        scaling_constants={"salary": 0.5, "commute": 0.3, "prestige": 0.2},
        independence_assumptions=[
            IndependenceAssumption(
                subset=frozenset({"salary", "commute"}),
                complement=frozenset({"prestige"}),
                kind="preferential", verified=True,
            ),
        ],
    )
    with pytest.raises(IndependenceNotVerified) as ei:
        dispatch(Job.MULTIOBJECTIVE, contract)
    msg = str(ei.value)
    # the two uncovered pairwise subsets must be named specifically
    assert "{prestige, salary}" in msg
    assert "{commute, prestige}" in msg
    assert ei.value.field == "independence_assumptions"


def test_n3_pairwise_implies_mutual():
    """c02 §3.4: for n=3 pairwise preferential independence is equivalent to mutual."""
    names = ["a", "b", "c"]
    all_attrs = frozenset(names)
    pairwise_only = [
        IndependenceAssumption(subset=s, complement=all_attrs - s,
                               kind="preferential", verified=True)
        for s in required_independence_subsets(all_attrs) if len(s) == 2
    ]
    # the singletons are NOT recorded, yet mutual independence holds via the shortcut
    assert mutual_independence_holds(pairwise_only, all_attrs, "preferential")
    assert uncovered_independence_subsets(pairwise_only, all_attrs, "preferential") == set()


def test_any_passing_test_no_longer_clears_the_gate():
    """The old gate was `any(t.passed)`: one pass among many failures cleared it."""
    all_attrs = frozenset({"a", "b", "c", "d"})
    one_only = [IndependenceAssumption(subset=frozenset({"a"}),
                                       complement=all_attrs - frozenset({"a"}),
                                       kind="preferential", verified=True)]
    assert not mutual_independence_holds(one_only, all_attrs, "preferential")


def test_flip_test_requires_prior_independence():
    with pytest.raises(ValueError):
        run_flip_test("straight", mutual_utility_independence_verified=False)


def test_flip_test_mappings():
    additive = run_flip_test(None, mutual_utility_independence_verified=True)
    assert additive.implied_form == "additive" and additive.k_yz_sign == 0
    straight = run_flip_test("straight", mutual_utility_independence_verified=True)
    assert straight.implied_form == "multiplicative" and straight.k_yz_sign == 1
    crossed = run_flip_test("crossed", mutual_utility_independence_verified=True)
    assert crossed.implied_form == "multiplicative" and crossed.k_yz_sign == -1
    with pytest.raises(ValueError):
        run_flip_test("sideways", mutual_utility_independence_verified=True)


def test_form_disagreement_is_audit_failure():
    """flip test says additive, sum(k_i)=1.3 -> INV-3 fails."""
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 0, 1), AttributeRange("b", 0, 1)],
        scaling_constants={"a": 0.7, "b": 0.6},          # Σk_i = 1.3 -> multiplicative
        independence_assumptions=_mutually_independent(["a", "b"]),
        flip_test_performed=True,
        flip_test_preferred_pairing=None,                 # indifferent -> additive
    )
    flip = run_flip_test(None, mutual_utility_independence_verified=True)
    result = check_independence_and_form(contract, flip, k_sum=1.3)
    assert result.passed is False
    assert result.invariant_id == "INV-3"
    assert "additive" in result.message and "multiplicative" in result.message


def test_form_agreement_passes():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 0, 1), AttributeRange("b", 0, 1)],
        scaling_constants={"a": 0.4, "b": 0.6},
        independence_assumptions=_mutually_independent(["a", "b"]),
        flip_test_performed=True,
        flip_test_preferred_pairing=None,
    )
    flip = run_flip_test(None, mutual_utility_independence_verified=True)
    assert check_independence_and_form(contract, flip, k_sum=1.0).passed


def test_empty_registry_is_stage2_not_stage1():
    """`[]` is elicited data; only `None` is absence of data (T4.4)."""
    base = dict(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 0, 1), AttributeRange("b", 0, 1)],
        scaling_constants={"a": 0.4, "b": 0.6},
    )
    # [] -> reaches Stage 2
    with pytest.raises(IndependenceNotVerified):
        dispatch(Job.MULTIOBJECTIVE, InputContract(independence_assumptions=[], **base))
    # None -> stopped at Stage 1
    with pytest.raises(ContractIncomplete) as ei:
        dispatch(Job.MULTIOBJECTIVE, InputContract(**base))
    assert ei.value.field == "independence_assumptions"


def test_empty_attributes_is_stage2_not_stage1():
    with pytest.raises(ContractIncomplete) as ei:
        dispatch(Job.MULTIOBJECTIVE, InputContract(
            job=Job.MULTIOBJECTIVE, independence_assumptions=[], scaling_constants={}))
    assert ei.value.field == "attributes"
    # [] falls through Stage 1 to the Stage 2 precondition
    from dominant_circuit import PreconditionViolation
    with pytest.raises(PreconditionViolation):
        dispatch(Job.MULTIOBJECTIVE, InputContract(
            job=Job.MULTIOBJECTIVE, attributes=[],
            independence_assumptions=[], scaling_constants={}))


def test_legacy_independence_test_still_converts():
    """IndependenceTest is deprecated but must keep working for one release."""
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 0, 1), AttributeRange("b", 0, 1)],
        scaling_constants={"a": 0.4, "b": 0.6},
        independence_tests=[
            IndependenceTest(pair=("a", "b"), method="flip_test", passed=True),
        ],
    )
    assert contract.independence_assumptions is not None
    assert len(contract.independence_assumptions) == 2   # both directions
    report = dispatch(Job.MULTIOBJECTIVE, contract)
    assert report.audit.passed


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
