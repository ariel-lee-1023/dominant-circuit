"""The five-stage interaction model, tested as a host AI would drive it.

Each test corresponds to a stage of the product's interaction design, and asserts
the capability a host needs in order to achieve that stage's effect — not merely
that the underlying function exists.
"""

import pytest

from dominant_circuit import (
    AttributeRange, AuditFailure, AuditResult, ContractIncomplete, FLIP_TEST_QUESTION,
    Horizon, INVARIANT_FIELDS, IndependenceNotVerified, Information, InputContract,
    InvariantResult, Job, NoOptimalStoppingRuleExists, Payoff, QUESTION_BANK,
    RiskAttitude, classify_job, dispatch, independence_questions, missing_fields,
    next_question, record_independence, run_flip_test,
)
from dominant_circuit.core.audit import require_audit_pass


# --- Stage 1: elicitation halts until boundary conditions are locked ---------------

def test_stage1_vague_input_yields_a_question_not_a_number():
    """An empty contract produces an askable question, never a default."""
    contract = InputContract()
    q = next_question(contract)
    assert q == QUESTION_BANK["job"]
    assert q.strip().endswith("?")
    with pytest.raises(ContractIncomplete):
        classify_job(contract)


def test_stage1_interrogation_terminates_and_locks_every_checkpoint():
    """Driving next_question() to completion fills the three checkpoints the
    design names: horizon, information type, hard constraints."""
    contract = InputContract(job=Job.STOPPING)
    answers = {
        "horizon": Horizon.FIXED_KNOWN,
        "payoff": Payoff.BEST_OR_NOTHING,
        "payoff_diverges": False,
        "information": Information.ORDINAL,
        "n": 50,
    }
    asked = []
    for _ in range(20):
        missing = missing_fields(contract)
        if not missing:
            break
        field = missing[0]
        asked.append(field)
        assert next_question(contract) == QUESTION_BANK[field]
        setattr(contract, field, answers[field])
    else:
        pytest.fail("elicitation did not terminate")

    assert missing_fields(contract) == []
    # the three checkpoints from the design, all explicitly asked
    assert "horizon" in asked
    assert "information" in asked
    assert "payoff_diverges" in asked
    assert dispatch(Job.STOPPING, contract).numeric["r_star"] == 19


def test_stage1_never_infers_an_unstated_field():
    """A contract missing one field cannot be computed, however complete it looks."""
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=50,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
    )
    with pytest.raises(ContractIncomplete) as ei:
        dispatch(Job.STOPPING, contract)
    assert ei.value.field == "payoff_diverges"


# --- Stage 2: verification rejects impossible premises ----------------------------

def test_stage2_rejects_diverging_payoff_premise():
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=50,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=True,
    )
    with pytest.raises(NoOptimalStoppingRuleExists):
        dispatch(Job.STOPPING, contract)


def test_stage2_independence_questions_are_askable_and_close_the_gate():
    """The flip-test checkpoint must be drivable: the host is told exactly which
    independence claims to ask about, and recording the answers opens the gate."""
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("salary", 40, 100),
                    AttributeRange("commute", 60, 10, monotonic_increasing=False)],
        scaling_constants={"salary": 0.65, "commute": 0.35},
        independence_assumptions=[],
    )

    # gate is shut, and the host is told what to ask
    with pytest.raises(IndependenceNotVerified):
        dispatch(Job.MULTIOBJECTIVE, contract)

    questions = independence_questions(contract)
    assert len(questions) == 2                       # {salary}, {commute}
    for subset, complement, question in questions:
        assert subset and complement
        assert subset.isdisjoint(complement)
        assert question.strip().endswith(")") or question.strip().endswith("?")
        assert next(iter(subset)) in question        # names the actual attribute

    # recording the answers closes it
    for subset, complement, _ in questions:
        contract.independence_assumptions.append(
            record_independence(subset, complement, contract.independence_kind,
                                verified=True, evidence="host elicited")
        )
    assert independence_questions(contract) == []
    assert dispatch(Job.MULTIOBJECTIVE, contract).audit.passed


def test_stage2_independence_questions_track_the_kind():
    """Under uncertainty the questions must be about utility, not preference."""
    attrs = [AttributeRange("a", 0, 1), AttributeRange("b", 0, 1)]
    certainty = InputContract(job=Job.MULTIOBJECTIVE, attributes=attrs,
                              independence_assumptions=[])
    uncertainty = InputContract(job=Job.MULTIOBJECTIVE, attributes=attrs,
                                independence_assumptions=[],
                                risk_attitude=RiskAttitude.AVERSE)
    assert "ranking of outcomes" in independence_questions(certainty)[0][2]
    assert "risk attitude" in independence_questions(uncertainty)[0][2]


def test_stage2_flip_test_question_is_a_real_question():
    assert FLIP_TEST_QUESTION.strip().endswith("?")
    assert "straight" in FLIP_TEST_QUESTION and "crossed" in FLIP_TEST_QUESTION
    # and the field it fills is elicitable
    assert "flip_test_preferred_pairing" in QUESTION_BANK


def test_stage2_flip_test_cannot_be_used_to_establish_independence():
    with pytest.raises(ValueError):
        run_flip_test("straight", mutual_utility_independence_verified=False)


# --- Stage 4: audit failure routes back to the right question ---------------------

def test_stage4_audit_failure_names_invariants_and_loop_back_fields():
    audit = AuditResult(results=[
        InvariantResult("INV-3", "independence_and_form", False,
                        message="form disagreement"),
        InvariantResult("INV-6", "finite_expectation", True),
    ])
    with pytest.raises(AuditFailure) as ei:
        require_audit_pass(audit)

    err = ei.value
    assert err.invariant_ids == ["INV-3"]
    assert err.invariants[0].message == "form disagreement"
    # exactly what to re-elicit, not a generic instruction
    assert "independence_assumptions" in err.fields
    assert err.field == err.fields[0]
    assert "independence_assumptions" in err.remedy
    assert "form disagreement" in str(err)


def test_stage4_every_invariant_has_a_loop_back_target():
    """No invariant may fail without telling the host what to re-ask."""
    for inv_id in ("INV-1", "INV-2", "INV-3", "INV-4", "INV-5", "INV-6", "INV-7"):
        assert INVARIANT_FIELDS.get(inv_id), f"{inv_id} has no loop-back fields"


def test_stage4_loop_back_fields_are_real_contract_fields():
    contract = InputContract()
    for inv_id, fields in INVARIANT_FIELDS.items():
        for name in fields:
            assert hasattr(contract, name), f"{inv_id} -> unknown field {name!r}"


# --- Stage 5: report carries an action and a stop-analyzing verdict ---------------

def _classical(n=50):
    return InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=n,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        recall_allowed=False, payoff_diverges=False,
    )


def test_stage5_action_is_an_instruction_not_a_dict():
    report = dispatch(Job.STOPPING, _classical())
    assert report.action
    assert str(report.decision) not in report.action
    # names the actual computed cutoff
    assert "19" in report.action and "50" in report.action


def test_stage5_every_engine_emits_an_action():
    stopping = dispatch(Job.STOPPING, _classical())

    multi = dispatch(Job.MULTIOBJECTIVE, InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("x", 0, 10), AttributeRange("y", 0, 10)],
        scaling_constants={"x": 0.5, "y": 0.5},
        independence_assumptions=[
            record_independence({"x"}, {"y"}, "preferential", True),
            record_independence({"y"}, {"x"}, "preferential", True),
        ],
        alternatives=[{"name": "A", "x": 8, "y": 8}, {"name": "B", "x": 2, "y": 2}],
    ))

    seq = dispatch(Job.SEQUENTIAL, InputContract(
        job=Job.SEQUENTIAL, horizon=Horizon.INFINITE_DISCOUNTED, gamma=0.9,
        markov_verified=True, states=["s0", "s1"], actions=["stay", "go"],
        reward={("s0", "go"): 1.0, ("s1", "stay"): 0.0},
        transition={("s0", "go"): {"s1": 1.0}, ("s0", "stay"): {"s0": 1.0},
                    ("s1", "go"): {"s1": 1.0}, ("s1", "stay"): {"s1": 1.0}},
    ))

    for report in (stopping, multi, seq):
        assert report.action, f"{report.formula_name} emits no action"
        assert len(report.action) > 30


def test_stage5_tells_the_user_when_to_stop_analyzing():
    report = dispatch(Job.STOPPING, _classical())
    assert report.analysis_is_complete is True
    assert "EXECUTE" in report.execution_note
    # and names the facts that would change the answer
    assert report.assumptions_to_confirm
    for entry in report.assumptions_to_confirm:
        assert entry.decision_changed


def test_stage5_withholds_permission_when_the_audit_failed():
    from dominant_circuit import OutputReport
    report = OutputReport(
        decision="x", formula_name="f", formula_latex="", citation="c01 §5",
        numeric={}, assumptions={}, sensitivity=[],
        audit=AuditResult(results=[
            InvariantResult("INV-1", "assumption_set_match", False, message="bad"),
        ]),
        action="do the thing",
    )
    assert report.analysis_is_complete is False
    assert "DO NOT EXECUTE" in report.execution_note
    assert "INV-1" in report.execution_note


def test_stage5_markdown_carries_the_execute_section():
    md = dispatch(Job.STOPPING, _classical()).to_markdown()
    assert "## Execute" in md
    assert "EXECUTE" in md
    # the action is what a reader sees under Decision
    assert md.index("## Decision") < md.index("Reject the first 18")
    assert "## Audit" in md and md.index("## Audit") < md.index("## Execute")


def test_stage5_to_dict_exposes_the_execution_verdict():
    d = dispatch(Job.STOPPING, _classical()).to_dict()
    assert d["analysis_is_complete"] is True
    assert "EXECUTE" in d["execution_note"]
    assert d["action"]
