"""Scripted host adapters, deliberately separate from live language evaluation.

Every utterance has a predeclared operation. Passing proves API state behavior,
not that a conversational model inferred a faithful operation from the utterance.
"""

from dataclasses import replace
import json
from pathlib import Path
import runpy
import pytest
from dominant_circuit import (
    AccountRelationship,
    AnalyticalResult,
    Boundary,
    DecisionDescription,
    Observation,
    ParticipantPosition,
    WorkingAccount,
    decode,
    dispatch,
    encode,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = runpy.run_path(str(ROOT / "examples/stage0_investigation.py"))
CASES = json.loads((ROOT / "tests/fixtures/stage0_conversations.json").read_text())[
    "cases"
]


def start():
    i = EXAMPLE["support_queue"]()
    i = i.propose_observation("tickets", EXAMPLE["ticket_plan"](i), "synthetic:plan")
    return i.record_analysis(
        "initial",
        AnalyticalResult(
            "queue delays",
            "qualitative account",
            "relevant",
            "Capacity may contribute; recurring demand is not assessed",
        ),
        (i.current_model_ref,),
        "synthetic:analysis",
    )


def apply(i, operation, utterance):
    if operation in {"start", "two_accounts", "handoff", "awaiting"}:
        i = start()
        if operation == "two_accounts":
            i = i.propose_account(
                "demand",
                WorkingAccount(
                    "Recurring demand",
                    ("reopens",),
                    Boundary(
                        ("product defects",),
                        ("training",),
                        ("relative contributions",),
                        "Capacity may also contribute",
                    ),
                    ("Unresolved defects may create repeat contacts",),
                    proposed_by="host",
                ),
                "synthetic:demand",
            )
            refs = (
                i.latest_ref("account", "capacity"),
                i.latest_ref("account", "demand"),
            )
            i = i.relate_accounts(
                "both",
                AccountRelationship(
                    refs, "complementary", "Neither mechanism excludes the other"
                ),
                "synthetic:relation",
            )
            i = i.propose_observation(
                "tickets",
                EXAMPLE["ticket_plan"](i, accounts=refs),
                "synthetic:two-account-plan",
            )
        elif operation == "handoff":
            i = i.handoff("comparison", EXAMPLE["offer_contract"]())
            c = i.get_handoff("comparison")
            i = i.record_report(
                "recommendation",
                dispatch(c.job, c, investigation=i),
                "comparison",
                "synthetic:report",
            )
        elif operation == "awaiting":
            i = i.await_observation(
                "tickets", "authorized manager", "synthetic:authorization"
            )
        return i
    if operation == "static":
        return EXAMPLE["simple_comparison"]()
    if operation in {"defects", "training", "both", "inconclusive"}:
        name = "defects" if operation == "defects" else operation
        i = EXAMPLE["record_episode"](
            i,
            name,
            utterance,
            missingness=(
                ("Repeat-contact records unavailable",)
                if operation == "inconclusive"
                else ()
            ),
        )
        outcome = {
            "defects": "repeat",
            "training": "training",
            "both": "both",
            "inconclusive": "inconclusive",
        }[operation]
        assessments = {
            "capacity": (
                "weakened"
                if operation == "defects"
                else (
                    "unresolved"
                    if operation == "inconclusive"
                    else "supported_within_scope"
                )
            )
        }
        if operation in {"both", "inconclusive"}:
            assessments["demand"] = assessments["capacity"]
        i = i.review_observation(
            name,
            outcome,
            assessments,
            (
                ("unresolved_evidence",)
                if operation == "inconclusive"
                else ("input_revision",)
            ),
            "Only the reported sample is assessed; relative contributions remain unknown.",
            "synthetic:review-" + name,
        )
        if operation == "defects":
            i = EXAMPLE["expand_demand"](i)
            i = i.propose_observation(
                "next", EXAMPLE["ticket_plan"](i), "synthetic:next"
            )
        elif operation == "training":
            i = i.record_analysis(
                "comparison",
                AnalyticalResult(
                    "resolution time",
                    "compare periods",
                    "relevant",
                    "Apparent slowdown under the reported definition",
                ),
                (i.current_model_ref, i.latest_ref("obs", name)),
                "synthetic:comparison",
            )
        elif operation == "both":
            refs = (
                i.latest_ref("account", "capacity"),
                i.latest_ref("account", "demand"),
            )
            i = i.relate_accounts(
                "both",
                AccountRelationship(
                    refs,
                    "complementary",
                    "Both are plausible; relative contributions remain unknown",
                ),
                "synthetic:revised-relation",
            )
        else:
            i = i.pause(
                "Accessible records do not distinguish accounts",
                "Authorized repeat-contact evidence becomes available",
                "synthetic:pause",
            )
        return i
    if operation == "measurement":
        original = i.get(i.latest_ref("obs", "training"))
        corrected = replace(
            original,
            finding=EXAMPLE["evidence"]("definition", utterance),
            context="New and old resolution-time definitions differ",
        )
        return i.correct_observation(
            "training",
            corrected,
            "synthetic:definition-change",
            "Reopened tickets changed comparability; revisit the diagnosis",
        )
    if operation == "counterexample":
        i = i.record_correction(
            "episode", "counterexample", utterance, "employee", "synthetic:episode"
        )
        old = i.get(i.current_model_ref)
        i = i.revise_account(
            "capacity",
            replace(
                old,
                mechanisms=old.mechanisms + ("Repeat demand may contribute",),
                boundary=Boundary(
                    ("training", "repeat contacts"),
                    (),
                    ("cause of recurrence",),
                    "The episode challenges a capacity-only boundary",
                ),
            ),
            ("boundary_revision",),
            i.latest_ref("correction", "episode"),
            "Retain the raw episode and broaden the working account",
        )
        i = i.acknowledge_correction(
            "episode",
            "Describe the available episode; this does not establish relative causes",
            "synthetic:acknowledge",
        )
        plan = replace(
            EXAMPLE["ticket_plan"](i),
            kind="exploratory",
            source="episode already available to the user",
            question="Describe what happened between the repeat contacts",
            method="Use the user's own episode, without restricted logs",
            possible_findings=tuple(
                f
                for f in EXAMPLE["ticket_plan"](i).possible_findings
                if f.finding_id in {"both", "inconclusive"}
            ),
        )
        return i.propose_observation("episode", plan, "synthetic:bounded-step")
    if operation == "goal":
        return i.revise_goal(
            DecisionDescription(
                "queue",
                utterance,
                objectives=["fewer repeat contacts", "sustainable workload"],
            ),
            "synthetic:new-goal",
            "User changed the objective",
        )
    if operation == "access":
        i = i.record_position(
            "employee",
            ParticipantPosition(
                "employee", "understand delays", can_access=False, can_authorize=False
            ),
            "synthetic:access",
        )
        i = i.propose_observation(
            "tickets",
            EXAMPLE["ticket_plan"](i, access="unavailable"),
            "synthetic:inaccessible-plan",
        )
        return i.pause(
            "User lacks log access and collection authority",
            "Access is granted or an accessible episode is offered",
            "synthetic:pause",
        )
    if operation == "hypothetical":
        return i  # Asking about possible findings is no evidence event.
    if operation == "conflict":
        i = i.record_position(
            "manager",
            ParticipantPosition(
                "manager", "close more tickets", "adopted", can_authorize=True
            ),
            "synthetic:manager",
        )
        i = i.record_position(
            "employee",
            ParticipantPosition(
                "employee",
                "sustainable workload and fewer repeat contacts",
                "disputed",
                affected=True,
                can_access=False,
                can_authorize=False,
            ),
            "synthetic:employee",
        )
        return EXAMPLE["record_episode"](
            i, "employee-report", utterance, participant="employee"
        )
    raise AssertionError(operation)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_conversation_trace(case, tmp_path):
    i = None
    trace = []
    for turn in case["turns"]:
        before = encode(i)
        previous = i
        i = apply(i, turn["adapter_operation"], turn["utterance"])
        if previous is not None:
            assert encode(previous) == before
            assert i.records[: len(previous.records)] == previous.records
        trace.append(
            dict(triggering_utterance=turn["utterance"], before=before, after=encode(i))
        )
    assert i.workflow in case["allowed_final_states"]
    for ref in case["expected_invalidations"]:
        assert not i.is_valid(ref)
    assert len(i.render_fields()) == 6
    assert all(
        a.assessment != "contradicted_under_stated_assumptions" for a in i.accounts
    )
    id = case["id"]
    if id in {"F01", "F09"}:
        assert len(i.get(i.current_model_ref).mechanisms) == 2
        assert (
            "recurring product defects" in i.get(i.current_model_ref).boundary.included
        )
    if id == "F02":
        assert (
            len(i.accounts) == 2 and i.relationships[0].relationship == "complementary"
        )
        assert all(
            a.assessment == "supported_within_scope" and a.assessment_scope
            for a in i.accounts
        )
    if id == "F03":
        assert i.pending_reviews and not i.is_valid(i.current_model_ref)
        assert (
            i.get("obs:training@1").finding.value
            != i.get("obs:training@2").finding.value
        )
    if id == "F04":
        assert all(a.assessment == "unresolved" for a in i.accounts)
        assert i.observations[0].missingness and i.unresolved_questions
    if id == "F05":
        loaded = decode(json.loads(json.dumps(encode(i))))
        assert (
            loaded.get("correction:episode@1")["text"] == case["turns"][-1]["utterance"]
        )
        assert loaded.current_model_ref != "account:capacity@1"
    if id == "F06":
        assert (
            i.current_model_ref == "account:capacity@1"
            and i.accounts[0].assessment == "unassessed"
        )
        assert i.revisions[-1].change_types == ("goal_revision",)
    if id == "F07":
        with pytest.raises(ValueError):
            i.await_observation(
                "tickets", "employee", "synthetic:unsupported-authority"
            )
        assert i.pause_reason and i.reopening_trigger
    if id == "F08":
        assert not i.accounts and i.selected_plan_ref is None
        assert i.get_report("comparison").decision["best_alternative"] == "A"
    if id == "F09":
        with pytest.raises(ValueError):
            i.get_handoff("comparison")
        assert i.get_report("recommendation").readiness.state == "blocked"
    if id == "F10":
        assert not i.observations and not i.revisions
        assert trace[-1]["before"] == trace[-1]["after"]
    if id == "F11":
        assert i.contested_goals and len(i.positions) == 2
        assert i.observations[0].reported_by == "employee"
        unresolved = i.handoff("contested", EXAMPLE["offer_contract"]())
        with pytest.raises(ValueError):
            unresolved.get_handoff("contested")
    artifact = dict(
        case_id=id,
        kind="deterministic_adapter",
        structured_states=trace,
        final_report=i.render_fields(),
        metrics=dict(
            actual_revisions=len(i.revisions),
            unresolved_retained=bool(i.unresolved_questions or i.pending_reviews),
            useful_next_step="requires human review",
            unsupported_certainty="requires human review",
            unnecessary_questions="requires live host",
            unnecessary_reframings="requires live host",
        ),
    )
    (tmp_path / f"{id}-trace.json").write_text(json.dumps(artifact, indent=2))


def test_paraphrase_adapter_preserves_revision_invariants():
    c = CASES[0]
    results = []
    for utterances in ([t["utterance"] for t in c["turns"]], c["paraphrases"]):
        i = None
        for t, u in zip(c["turns"], utterances):
            i = apply(i, t["adapter_operation"], u)
        results.append(i)
    assert results[0].accounts == results[1].accounts
    assert (
        results[0].observations[0].finding.value
        != results[1].observations[0].finding.value
    )


@pytest.mark.parametrize("order", [("training", "defects"), ("defects", "training")])
def test_equivalent_evidence_order_retains_both_mechanisms(order):
    i = start()
    for name in order:
        i = EXAMPLE["record_episode"](
            i,
            name,
            "Training costs" if name == "training" else "Repeat contacts about defects",
        )
        i = i.review_observation(
            name,
            "training" if name == "training" else "repeat",
            {"capacity": "unresolved"},
            ("unresolved_evidence",),
            "Contributions unresolved; retain both observed patterns",
            "synthetic:order-review-" + name,
        )
        if name == "defects":
            i = EXAMPLE["expand_demand"](i)
        i = i.propose_observation(
            "tickets", EXAMPLE["ticket_plan"](i), "synthetic:replan-" + name
        )
    assert len(i.accounts[0].mechanisms) == 2
    assert {o.finding.value for o in i.observations} == {
        "Training costs",
        "Repeat contacts about defects",
    }
    assert i.accounts[0].assessment in {"unassessed", "unresolved"}
