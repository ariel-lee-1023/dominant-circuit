"""翻盘检验 — the overturn test as the operational definition of weight.

Weight is the magnitude of causal control a factor exerts over the outcome, given a
concrete goal, a time scale, and defined objects of comparison. There is no standard
answer: it depends entirely on the objective function. So the library cannot rank
factors by importance in the abstract — it can only answer, for a stated goal, the
one question that terminates:

    Is the presence or absence of this factor sufficient to overturn my conclusion?

If not, it is a high-order small quantity and belongs outside the dominant equation.
"""

import pytest

from dominant_circuit import (
    AttributeRange, ContractIncomplete, Horizon, Information, InputContract, Job,
    Payoff, asymptotic_cutoff, optimal_cutoff, record_independence,
)
from dominant_circuit.core.elicit import (
    WEIGHT_PREREQUISITES, elicitation_plan, overturn_test, screenable_fields,
)


def _stopping(n=50, **kw):
    base = dict(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=n,
                information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
                payoff_diverges=False)
    base.update(kw)
    return InputContract(**base)


# --- weight has prerequisites -------------------------------------------------------

def test_weight_is_undefined_before_the_goal_is_stated():
    """A factor has no weight until there is an objective function to weigh it
    against. The test refuses rather than inventing a baseline."""
    with pytest.raises(ContractIncomplete) as ei:
        overturn_test(InputContract(), "recall_allowed")
    assert ei.value.field == "job"

    # job known, goal/time-scale not yet
    partial = InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=50)
    with pytest.raises(ContractIncomplete) as ei:
        overturn_test(partial, "recall_allowed")
    assert "Weight is undefined" in str(ei.value)


def test_the_three_prerequisites_are_never_screenable():
    """给定目标、时间尺度、比较对象 are not factors to be weighed — they are what
    makes weighing possible. They must never appear as droppable."""
    contract = _stopping()
    screenable = set(screenable_fields(contract))
    for group, fields in WEIGHT_PREREQUISITES.items():
        assert screenable.isdisjoint(fields), f"{group} leaked into screenable"
    assert set(WEIGHT_PREREQUISITES) == {"goal", "time_scale", "comparison_set"}


def test_plan_refuses_to_screen_before_the_contract_is_complete():
    plan = elicitation_plan(InputContract(job=Job.STOPPING))
    assert plan["required"], "an incomplete contract must still have required fields"
    assert plan["load_bearing"] == [] and plan["droppable"] == []
    assert "Weight is undefined" in plan["note"]


# --- the same factor has different weight for different goals ---------------------

@pytest.mark.parametrize("n,expected_overturn", [
    (50, True),    # exact 19 vs asymptotic 18 — the choice changes the answer
    (45, False),   # both 17 — the choice cannot change the answer
    (48, False),   # both 18
    (102, False),  # both 38
])
def test_exact_vs_asymptotic_weight_depends_on_the_pool_size(n, expected_overturn):
    """There is no standard answer for weight. Whether "use the exact computation or
    the famous 37%?" matters is decided by the overturn test for THIS n, not by a
    rule of thumb — and it genuinely goes both ways."""
    differs = optimal_cutoff(n)[0] != asymptotic_cutoff(n)[0]
    assert differs is expected_overturn, "test fixture no longer exercises both cases"

    result = overturn_test(_stopping(n), "exact_finite_n")
    assert result.overturns is expected_overturn
    assert result.is_small_quantity is (not expected_overturn)


def test_a_droppable_factor_says_throw_it_out():
    result = overturn_test(_stopping(45), "exact_finite_n")
    assert result.is_small_quantity
    assert "high-order small quantity" in result.verdict
    assert "dominant equation" in result.verdict


def test_a_load_bearing_factor_says_elicit_it():
    result = overturn_test(_stopping(50), "recall_allowed")
    assert result.overturns
    assert "load-bearing" in result.verdict
    assert result.baseline_decision is not None


def test_search_cost_has_no_weight_under_a_best_or_nothing_goal():
    """Not because the number is small — because the factor has zero causal control
    over this objective function. Weight is relative to the goal."""
    result = overturn_test(_stopping(), "search_cost")
    assert result.is_small_quantity
    assert result.outcomes, "probes must actually have been run"


# --- a refusal counts as an overturn ----------------------------------------------

def test_a_refusal_counts_as_an_overturn():
    """If setting a factor makes the problem uncomputable or uncalibrated, that
    factor is emphatically load-bearing — not neutral."""
    contract = _stopping(rejection_prob=0.5)
    # adding recall to a rejection contract is uncalibrated (c01 §7) -> refusal
    result = overturn_test(contract, "recall_allowed")
    assert result.overturns
    assert any(outcome == "REFUSED" for _, outcome in result.outcomes)


def test_explicit_probes_override_the_defaults():
    contract = _stopping()
    # a probe that changes nothing must not report an overturn
    quiet = overturn_test(contract, "n", probes=[{"n": 50}])
    assert quiet.is_small_quantity
    # ...and one that does must
    loud = overturn_test(contract, "n", probes=[{"n": 9}])
    assert loud.overturns


def test_unknown_field_does_not_silently_claim_no_weight():
    """Absence of a probe is not evidence of absence of weight, and the verdict
    must say so rather than quietly reporting 'droppable'."""
    result = overturn_test(_stopping(), "risk_varies_with_level")
    assert result.is_small_quantity          # no overturn demonstrated...
    assert "No probe defined" in result.verdict   # ...but the reason is stated
    assert "rather than assuming" in result.verdict


# --- the plan is the answer to "am I done asking?" -------------------------------

def test_plan_separates_load_bearing_from_droppable():
    plan = elicitation_plan(_stopping(50))
    assert plan["required"] == []
    assert "recall_allowed" in plan["load_bearing"]
    assert "search_cost" in plan["droppable"]
    assert set(plan["load_bearing"]).isdisjoint(plan["droppable"])
    assert "Ask only about `load_bearing`" in plan["note"]


def test_plan_shrinks_when_a_factor_loses_its_weight():
    """The whole point: at n=45 the exact/asymptotic choice stops being worth a
    question, so the host asks one fewer thing."""
    at_50 = elicitation_plan(_stopping(50))
    at_45 = elicitation_plan(_stopping(45))
    assert "exact_finite_n" in at_50["load_bearing"]
    assert "exact_finite_n" in at_45["droppable"]
    assert len(at_45["load_bearing"]) < len(at_50["load_bearing"])


def test_plan_works_for_the_other_two_jobs():
    multi = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("a", 0, 10), AttributeRange("b", 0, 10)],
        scaling_constants={"a": 0.4, "b": 0.6},
        independence_assumptions=[
            record_independence({"a"}, {"b"}, "preferential", True),
            record_independence({"b"}, {"a"}, "preferential", True),
        ],
        alternatives=[{"name": "A", "a": 8, "b": 3}, {"name": "B", "a": 3, "b": 8}],
    )
    plan = elicitation_plan(multi)
    assert plan["required"] == []
    assert set(plan["load_bearing"]) | set(plan["droppable"])

    seq = InputContract(
        job=Job.SEQUENTIAL, horizon=Horizon.INFINITE_DISCOUNTED, gamma=0.9,
        markov_verified=True, states=["s0", "s1"], actions=["stay", "go"],
        reward={("s0", "go"): 1.0, ("s1", "stay"): 2.0},
        transition={("s0", "go"): {"s1": 1.0}, ("s0", "stay"): {"s0": 1.0},
                    ("s1", "go"): {"s1": 1.0}, ("s1", "stay"): {"s1": 1.0}},
    )
    plan = elicitation_plan(seq)
    assert plan["required"] == []


def test_overturn_test_does_not_mutate_the_contract():
    contract = _stopping()
    before = (contract.recall_allowed, contract.exact_finite_n, contract.n)
    overturn_test(contract, "recall_allowed")
    elicitation_plan(contract)
    assert (contract.recall_allowed, contract.exact_finite_n, contract.n) == before


def test_design_md_weight_table_matches_the_engine():
    """DESIGN.md's worked screening table must be computed, not plausible."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    text = (root / "DESIGN.md").read_text(encoding="utf-8")
    start = text.index("## Weight (权重) and the overturn test")
    section = text[start:text.index("\n## ", start + 10)]

    rows = re.findall(r"\|\s*n = (\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", section)
    assert rows, "DESIGN.md has no screening table"
    for n_str, exact_str, asym_str in rows:
        n = int(n_str)
        assert optimal_cutoff(n)[0] == int(exact_str), f"n={n} exact"
        assert asymptotic_cutoff(n)[0] == int(asym_str), f"n={n} asymptotic"
        overturns = overturn_test(_stopping(n), "exact_finite_n").overturns
        assert overturns is (int(exact_str) != int(asym_str)), f"n={n} verdict"
    # the table must exercise both verdicts, or it proves nothing
    verdicts = {optimal_cutoff(int(r[0]))[0] != asymptotic_cutoff(int(r[0]))[0] for r in rows}
    assert verdicts == {True, False}
