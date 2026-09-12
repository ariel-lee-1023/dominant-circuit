"""Deterministic Stage 0 evidence-return invariants; live language tests are separate."""

from dataclasses import replace
import json
import pytest
from dominant_circuit import (
    ConsequentialInput,
    DecisionDescription,
    encode,
    decode,
    dispatch,
    Job,
)
from dominant_circuit.core.investigation import (
    Investigation,
    WorkingAccount,
    Boundary,
    ObservationPlan,
    PossibleFinding,
    Observation,
    AnalyticalResult,
    AccountRelationship,
    ParticipantPosition,
)
from test_remediation import offers


def source(key, value, origin="user_report", event=None):
    return ConsequentialInput(
        key, value, origin=origin, evidence_ref=event or "host:" + key, scope="queue"
    )


def started():
    i = Investigation.begin(
        "queue",
        DecisionDescription(
            "queue", "Understand slow support", objectives=["reduce backlog"]
        ),
        "host:goal",
    )
    a = WorkingAccount(
        "Capacity and training",
        ("arrivals", "processing"),
        Boundary(
            ("staffing", "training"),
            ("product defects",),
            ("repeat contact generation",),
            "Recurring defects could generate demand outside the staffing measures.",
        ),
        ("training reduces available processing time",),
        proposed_by="host",
    )
    return i.propose_account("capacity", a, "host:proposal")


def plan(i, access="available", kind="discriminating"):
    return ObservationPlan(
        "Compare repeat contacts with training periods",
        kind,
        (i.current_model_ref,),
        ("training reduces processing",),
        "ticket sample",
        "Review issue and reopening tags",
        (
            PossibleFinding(
                "repeat",
                "Many repeated defect-related contacts",
                "Expand demand boundary",
            ),
            PossibleFinding(
                "training",
                "Delay concentrated in training periods",
                "Capacity remains plausible",
            ),
            PossibleFinding(
                "inconclusive",
                "Records fit both or are unavailable",
                "Retain uncertainty; describe accessible episodes",
            ),
        ),
        access=access,
        effort_assessment="manageable",
        owner=None,
        effort="small manual sample",
        collection_effects="Tagging may change reporting",
        omission_challenge="Review reasons for repeat contacts, not just handling time",
    )


def planned():
    i = started()
    return i.propose_observation("tickets", plan(i), "host:plan")


def observed(
    i,
    key="defects",
    finding="Repeated contacts about unresolved defects",
    missingness=(),
):
    obs = Observation(
        source(key, finding),
        "Support queue during two weeks",
        missingness=missingness,
        selection_limits=("Convenience sample",),
        raw_episode_ref="host:episode-" + key,
        plan_ref=i.latest_ref("plan", "tickets"),
    )
    return i.receive_observation(key, obs)


def test_planned_evidence_cannot_be_reviewed_as_obtained():
    i = planned().await_observation("tickets", "manager", "host:authorization")
    assert i.workflow == "awaiting_observation"
    assert i.get(i.current_model_ref).assessment == "unassessed"
    with pytest.raises(ValueError):
        i.review_observation(
            "tickets",
            "repeat",
            {"capacity": "supported_within_scope"},
            ("input_revision",),
            "No actual result",
            "host:review",
        )
    assert len(i.observations) == 0
    assert len(i.render_fields()) == 6
    assert "ready to execute" not in i.to_markdown().lower()


def test_evidence_can_revise_boundary_and_invalidate_selectively():
    i = planned()
    i = i.record_analysis(
        "capacity-note",
        AnalyticalResult(
            "explain queue", "qualitative review", "relevant", "Capacity may contribute"
        ),
        (i.current_model_ref,),
        "host:analysis",
    )
    old_analysis = i.latest_ref("analysis", "capacity-note")
    old_model = i.current_model_ref
    i = observed(i)
    assert i.workflow == "reviewing" and not i.is_valid(old_analysis)
    i = i.review_observation(
        "defects",
        "repeat",
        {"capacity": "weakened"},
        ("boundary_revision", "mechanism_revision"),
        "Demand generation was omitted; capacity may still contribute",
        "host:review",
    )
    revised = replace(
        i.get(i.current_model_ref),
        boundary=Boundary(
            ("staffing", "training", "recurring defects"),
            (),
            ("relative contributions",),
            "Tag coverage is incomplete",
        ),
        mechanisms=(
            "training reduces available capacity",
            "unresolved defects create repeat demand",
        ),
        assessment="unassessed",
    )
    i = i.revise_account(
        "capacity",
        revised,
        ("boundary_revision",),
        "obs:defects@1",
        "Expand to include repeat demand",
    )
    assert i.current_model_ref != old_model
    assert not i.is_valid(old_model) and not i.is_valid(old_analysis)
    assert i.get(old_model).boundary.external == ("product defects",)
    assert len(i.observations) == 1 and i.observations[0].raw_episode_ref
    assert "what changed" in i.last_update().lower()


def test_inconclusive_missing_evidence_does_not_confirm():
    i = observed(
        planned(), finding=None, missingness=("Repeat-contact records unavailable",)
    )
    with pytest.raises(ValueError):
        i.review_observation(
            "defects",
            "repeat",
            {"capacity": "supported_within_scope"},
            ("input_revision",),
            "No contradiction",
            "host:review",
        )
    i = i.review_observation(
        "defects",
        "inconclusive",
        {"capacity": "unresolved"},
        ("unresolved_evidence",),
        "Cannot distinguish accounts",
        "host:review",
    )
    assert i.get(i.current_model_ref).assessment == "unresolved"
    assert i.observations[0].finding.value is None


def test_untranslated_counterexample_survives_and_disagreement_is_not_consensus():
    i = started().record_correction(
        "episode",
        "counterexample",
        "I cannot draw this, but yesterday the same person contacted us five times",
        "employee",
        "host:episode",
    )
    i = i.record_position(
        "employee",
        ParticipantPosition(
            "employee", "fewer repeat contacts", "disputed", affected=True
        ),
        "host:employee",
    )
    i = i.record_position(
        "manager",
        ParticipantPosition(
            "manager", "close more tickets", "adopted", can_authorize=True
        ),
        "host:manager",
    )
    loaded = decode(json.loads(json.dumps(encode(i))))
    assert loaded.get(loaded.latest_ref("correction", "episode"))["text"].startswith(
        "I cannot draw"
    )
    assert loaded.contested_goals
    assert len(loaded.positions) == 2
    assert loaded.get(loaded.current_model_ref).assessment == "unassessed"


def test_goal_revision_is_not_causal_falsification():
    i = planned()
    old = i.current_model_ref
    old_plan = i.latest_ref("plan", "tickets")
    i = i.revise_goal(
        DecisionDescription("queue", "Reduce repeat contacts and workload"),
        "host:new-goal",
        "Changed purpose",
    )
    assert i.current_model_ref == old and i.get(old).assessment == "unassessed"
    assert not i.is_valid(old_plan)
    assert i.revisions[-1].change_types == ("goal_revision",)


def test_unavailable_step_can_pause_and_reopen_without_claiming_settlement():
    i = started()
    i = i.propose_observation("tickets", plan(i, access="unavailable"), "host:plan")
    assert i.workflow == "drafted"
    with pytest.raises(ValueError):
        i.await_observation("tickets", "manager", "host:authorization")
    i = i.pause(
        "No access to repeat-contact logs", "Access becomes available", "host:defer"
    )
    assert i.workflow == "paused"
    i = i.reopen("host:return")
    assert (
        i.workflow == "drafted"
        and i.get(i.current_model_ref).assessment == "unassessed"
    )


def test_formal_claims_require_prerequisites_and_never_self_certify():
    i = started()
    with pytest.raises(ValueError):
        i.record_analysis(
            "identification",
            AnalyticalResult(
                "",
                "Pearl",
                "relevant",
                "identified",
                analysis_type="identification",
                status="formally_checked",
            ),
            (i.current_model_ref,),
            "host:claim",
        )
    i = i.record_analysis(
        "identification",
        AnalyticalResult(
            "effect of training",
            "qualitative graph discussion",
            "relevant",
            "Unresolved",
            analysis_type="identification",
            model_spec="graph:v1",
            observable_set=("handling time",),
            status="qualitative",
        ),
        (i.current_model_ref,),
        "host:discussion",
    )
    assert i.get(i.latest_ref("analysis", "identification")).status == "qualitative"
    with pytest.raises(ValueError):
        i.record_analysis(
            "stability",
            AnalyticalResult(
                "queue length",
                "Page",
                "relevant",
                "stable",
                analysis_type="stability",
                model_spec="description",
                status="formally_checked",
            ),
            (i.current_model_ref,),
            "host:claim",
        )


def test_complementary_accounts_need_no_forced_exclusivity():
    i = started()
    i = i.propose_account(
        "defects",
        WorkingAccount(
            "Demand generation",
            ("reopens",),
            Boundary(("defects",), ("staffing",), (), "Capacity may also matter"),
            ("defects cause repeated contacts",),
        ),
        "host:demand",
    )
    relation = AccountRelationship(
        (i.latest_ref("account", "capacity"), i.latest_ref("account", "defects")),
        "complementary",
        "Both mechanisms can operate",
    )
    i = i.relate_accounts("both", relation, "host:relation")
    assert len(i.accounts) == 2
    assert i.relationships[0].relationship == "complementary"


def test_simple_static_handoff_bypasses_investigation_and_is_guarded():
    c = offers()
    d = DecisionDescription(
        "offers", "Compare offers", problem_types=["static_comparison"]
    )
    i = Investigation.begin("offers", d, "host:goal")
    i = i.handoff("compare", c, unresolved_conditions=())
    contract = i.get_handoff("compare")
    assert not i.accounts
    with pytest.raises(ValueError):
        dispatch(Job.MULTIOBJECTIVE, contract)
    assert (
        dispatch(Job.MULTIOBJECTIVE, contract, investigation=i).decision[
            "best_alternative"
        ]
        == "A"
    )
    i = i.revise_goal(
        replace(d, question="Compare under another preference"),
        "host:revision",
        "Preference changed",
    )
    with pytest.raises(ValueError):
        dispatch(Job.MULTIOBJECTIVE, contract, investigation=i)
    with pytest.raises(ValueError):
        i.get_handoff("compare")


def test_pending_evidence_blocks_old_handoff_and_roundtrip_does_not_reactivate():
    i = planned()
    i = i.handoff("compare", offers(), unresolved_conditions=())
    c = i.get_handoff("compare")
    i = observed(i)
    with pytest.raises(ValueError):
        dispatch(Job.MULTIOBJECTIVE, c, investigation=i)
    imported = decode(json.loads(json.dumps(encode(i))))
    assert imported.pending_reviews
    with pytest.raises(ValueError):
        imported.get_handoff("compare")


def test_history_and_branches_do_not_mutate_predecessors():
    i = planned()
    before = encode(i)
    branch = i.branch("try-demand")
    assert encode(i) == before and branch.scenario_id == "try-demand"
    assert branch.records == i.records
    copy = i.get(i.current_model_ref)
    assert copy.assessment == "unassessed"


def test_workflow_cannot_skip_feasibility_or_collection_authorization():
    i = started()
    with pytest.raises(ValueError):
        replace(i, workflow="ready_to_observe")
    with pytest.raises(ValueError):
        replace(planned(), workflow="awaiting_observation")
    with pytest.raises(ValueError):
        planned().pause("", "", "host:pause")


def test_measurement_correction_invalidates_prior_assessment_and_preserves_original():
    i = observed(planned(), finding="Mean resolution time increased")
    i = i.review_observation(
        "defects",
        "training",
        {"capacity": "supported_within_scope"},
        ("input_revision",),
        "Only a descriptive sample",
        "host:review",
    )
    old_model = i.current_model_ref
    i = i.record_analysis(
        "comparison",
        AnalyticalResult(
            "old vs new resolution time",
            "compare definitions",
            "relevant",
            "An apparent increase",
        ),
        (old_model, "obs:defects@1"),
        "host:comparison",
    )
    original = i.get("obs:defects@1")
    corrected = replace(
        original,
        finding=source("metric", "The newer definition includes reopened tickets"),
        context="Definitions differ between the two periods",
    )
    i = i.correct_observation(
        "defects",
        corrected,
        "host:metric-correction",
        "The measurement is not comparable",
    )
    assert i.get("obs:defects@1") == original
    assert not i.is_valid(old_model)
    assert not i.is_valid(i.latest_ref("analysis", "comparison"))
    assert i.revisions[-1].change_types == ("measurement_correction",)


def test_reports_are_invalidated_with_handoff_and_history_is_retained():
    i = planned().handoff("comparison", offers())
    c = i.get_handoff("comparison")
    r = dispatch(c.job, c, investigation=i)
    i = i.record_report("recommendation", r, "comparison", "host:output")
    i = observed(i)
    assert i.get_report("recommendation").readiness.state == "blocked"
    assert i.get(i.latest_ref("report", "recommendation")).decision == r.decision


def test_no_empty_acknowledgement_erases_a_counterexample():
    i = started().record_correction(
        "counterexample",
        "counterexample",
        "A concrete mismatch",
        "worker",
        "host:mismatch",
    )
    with pytest.raises(ValueError):
        i.acknowledge_correction("counterexample", "", "host:review")


def test_unrelated_analysis_survives_scoped_evidence_return():
    i = planned()
    i = i.propose_account(
        "separate",
        WorkingAccount(
            "Separate process",
            ("another queue",),
            Boundary(("another queue",), (), (), "No shared mechanism is asserted"),
            ("Separate processing",),
        ),
        "host:separate",
    )
    i = i.record_analysis(
        "unaffected",
        AnalyticalResult(
            "another queue", "qualitative", "relevant", "Unrelated result"
        ),
        (i.latest_ref("account", "separate"),),
        "host:other-analysis",
    )
    i = observed(i)
    assert i.is_valid(i.latest_ref("analysis", "unaffected"))


def test_import_preserves_exact_historical_report_but_blocks_current_use():
    i = planned().handoff("compare", offers())
    c = i.get_handoff("compare")
    i = i.record_report(
        "result", dispatch(c.job, c, investigation=i), "compare", "host:result"
    )
    loaded = decode(json.loads(json.dumps(encode(i))))
    assert encode(loaded.records) == encode(i.records)
    assert loaded.get_report("result").readiness.state == "blocked"
    with pytest.raises(ValueError):
        loaded.get_handoff("compare")


def test_later_review_keeps_prior_evidence_dependencies():
    i = observed(planned(), key="first")
    i = i.review_observation(
        "first",
        "repeat",
        {"capacity": "weakened"},
        ("input_revision",),
        "First sample",
        "host:first-review",
    )
    i = i.propose_observation("tickets", plan(i), "host:new-plan")
    i = observed(i, key="second")
    i = i.review_observation(
        "second",
        "training",
        {"capacity": "supported_within_scope"},
        ("input_revision",),
        "Both samples inform this assessment",
        "host:second-review",
    )
    assert set(i._record(i.current_model_ref).dependencies) == {
        "obs:first@1",
        "obs:second@1",
    }
    correction = replace(
        i.get("obs:first@1"),
        finding=source("first", "The earlier sample was mislabelled"),
    )
    i = i.correct_observation(
        "first", correction, "host:correct", "The first sample changed"
    )
    assert not i.is_valid(i.current_model_ref)


def test_new_account_invalidates_an_existing_handoff():
    i = planned().handoff("compare", offers())
    i = i.propose_account(
        "demand",
        WorkingAccount(
            "Demand",
            ("reopens",),
            Boundary(("defects",), (), (), "Training remains possible"),
            ("Defects may generate demand",),
        ),
        "host:new-account",
    )
    with pytest.raises(ValueError):
        i.get_handoff("compare")


def test_cycle_can_finish_with_observation_and_resume_without_promoting_truth():
    i = planned().close_cycle(
        "A bounded observation is enough for this turn", "host:end"
    )
    assert (
        i.workflow == "closed_for_current_purpose"
        and i.accounts[0].assessment == "unassessed"
    )
    i = i.reopen("host:return")
    assert i.current_model_ref == "account:capacity@1" and i.workflow == "drafted"
    i = i.record_correction(
        "mismatch", "uncertainty", "Not sure this fits", "user", "host:uncertain"
    )
    with pytest.raises(ValueError):
        i.close_cycle("Ignore the correction", "host:end")


def test_unavailable_or_unverified_methods_do_not_become_certificates():
    from dominant_circuit import migrate_stage0_snapshot

    with pytest.raises(ValueError):
        AnalyticalResult(
            "effect",
            "identification",
            "relevant",
            "identified",
            status="external_unverified",
            analysis_type="identification",
            model_spec="graph",
            external_certificate_ref="source",
        )
    a = AnalyticalResult(
        "effect",
        "external identification",
        "unresolved",
        "Needs external validation",
        reason="No verifier here",
        status="external_unverified",
        analysis_type="identification",
        model_spec="graph",
        observable_set=("x", "y"),
        external_certificate_ref="source",
    )
    assert a.status == "external_unverified"
    with pytest.raises(ValueError):
        AnalyticalResult("target", "method", "inapplicable", "not run")
    snapshot = planned().render_fields()
    migrated = migrate_stage0_snapshot(snapshot)
    assert migrated["historical_snapshot"] == snapshot and not migrated["observations"]
    assert migrated["investigation_history"] == "unknown"


def test_late_evidence_on_old_plan_invalidates_current_handoff():
    i = observed(planned())
    i = i.review_observation(
        "defects",
        "repeat",
        {"capacity": "weakened"},
        ("input_revision",),
        "Demand possible",
        "host:review",
    )
    i = i.handoff("compare", offers())
    i = observed(i, key="late")  # The original plan names the first model revision.
    i = i.review_observation(
        "late",
        "inconclusive",
        {},
        ("unresolved_evidence",),
        "Cannot distinguish accounts",
        "host:late-review",
    )
    with pytest.raises(ValueError):
        i.get_handoff("compare")


def test_unknown_effort_does_not_establish_observation_readiness():
    i = started()
    unknown = replace(plan(i), effort_assessment="unknown", effort=None)
    i = i.propose_observation("tickets", unknown, "host:unknown-effort")
    assert i.workflow == "drafted"
    with pytest.raises(ValueError):
        i.await_observation("tickets", "manager", "host:authorization")
