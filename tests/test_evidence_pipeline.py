"""Stateful, deterministic host-adapter evaluations and acceptance tests."""

import json
from dataclasses import fields, replace
import pytest
from dominant_circuit import dispatch, Job, InputContract, Horizon, AuditResult
from dominant_circuit.core.evidence import (
    ConsequentialInput,
    Constraint,
    DecisionDescription,
    DecisionSession,
    PreferenceRevision,
    TranslationRecord,
    translate_decision,
    encode,
    decode,
)
from dominant_circuit.core.robustness import WeightRegion
from dominant_circuit.core.readiness import COMPUTATIONAL_FIELDS
from dominant_circuit.core.errors import PreconditionViolation, UnclassifiedVariant
from dominant_circuit.engines.sequential import value_iteration, belief_update
from test_remediation import offers, mdp, stopping


def evidence(key, value, **kw):
    defaults = dict(
        origin="user_report",
        evidence_ref="host:event-1",
        acceptance="accepted_for_this_decision",
        scope="decision-1",
        adoption_event="host:event-1",
    )
    defaults.update(kw)
    return ConsequentialInput(key, value, **defaults)


def supported(c):
    c.decision_id = "decision-1"
    c.provenance = {
        f.name: evidence(f.name, getattr(c, f.name))
        for f in fields(c)
        if f.name not in COMPUTATIONAL_FIELDS and getattr(c, f.name) is not None
    }
    c.uncertainty_treatment = evidence(
        "residual-choice", "Adopt this scoped comparison despite residual uncertainty"
    )
    return c


def region(x=(0.49, 0.51), y=(0.49, 0.51)):
    return WeightRegion(
        {"x": x, "y": y},
        "host:weights",
        "decision-1",
        attribute_ranges={"x": (0, 1), "y": (0, 1)},
    )


@pytest.mark.parametrize("budget", [0, -1, 1.5, True])
def test_invalid_budget(budget):
    with pytest.raises(PreconditionViolation):
        dispatch(Job.SEQUENTIAL, mdp(k_max=budget))


@pytest.mark.parametrize("tol", [0, -1, float("nan"), float("inf")])
def test_invalid_tolerance(tol):
    with pytest.raises(PreconditionViolation):
        dispatch(Job.SEQUENTIAL, mdp(tolerance=tol))


def test_discount_endpoints_terminal_and_certificate():
    c = mdp()
    for gamma in (0.0, 0.999999):
        r = dispatch(Job.SEQUENTIAL, replace(c, gamma=gamma, k_max=5))
        assert r.decision["termination_reason"] == "converged"
        assert r.decision["value_error_bound"] == 0
    result = value_iteration(["end"], ["a"], {}, {}, 0.9, terminal_states=["end"])
    assert result.policy == {"end": None} and result.bellman_residual == 0
    c = replace(c, horizon=Horizon.FINITE_SUM)
    with pytest.raises(UnclassifiedVariant):
        dispatch(c.job, c)


@pytest.mark.parametrize(
    "change",
    [
        {"transition": {}},
        {"reward": {}},
        {"transition": {("start", "take"): {"ghost": 1.0}}},
        {"transition": {("start", "take"): {"end": 0.9}}},
        {"reward": {("start", "take"): float("nan")}},
    ],
)
def test_malformed_mdp(change):
    with pytest.raises(PreconditionViolation):
        dispatch(Job.SEQUENTIAL, replace(mdp(), **change))


def test_impossible_observation_preserves_unknown():
    with pytest.raises(PreconditionViolation):
        belief_update({"a": 0.7, "b": 0.3}, "impossible", {"a": 0.0, "b": 0.0})
    with pytest.raises(PreconditionViolation):
        belief_update({"a": 1.2, "b": -0.2}, "o", {"a": 1.0, "b": 1.0})
    with pytest.raises(UnclassifiedVariant):
        belief_update({"a": 1.0}, "o", {"a": 1.0}, transition={})


def test_feasibility_precedes_ranking_and_never_relaxes():
    c = offers()
    c.alternatives[0]["pickup"] = 18
    c.alternatives[1]["pickup"] = 16
    c.constraints = [
        Constraint("pickup", "pickup", "<=", 17, evidence("pickup", 17), "decision-1")
    ]
    r = dispatch(c.job, c)
    assert r.decision["best_alternative"] == "B"
    del c.alternatives[1]["pickup"]
    r = dispatch(c.job, c)
    assert r.decision["best_alternative"] is None
    assert r.decision["feasibility"]["B"]["satisfied"] is None
    assert r.readiness.state == "blocked"
    assert c.constraints[0].limit == 17


@pytest.mark.parametrize("bad", [None, float("nan"), 2.0, "oops"])
def test_missing_malformed_and_out_of_range_attribute(bad):
    c = offers()
    c.alternatives[0]["x"] = bad
    with pytest.raises(PreconditionViolation):
        dispatch(c.job, c)


def test_weight_region_switch_and_certificate():
    c = offers(weight_region=region())
    r = dispatch(c.job, c).decision["robustness"]
    assert r["outcome"] == "changes_decision" and not r["robust_winners"]
    assert r["coverage"] == "whole_domain"
    stable = dispatch(
        c.job, replace(c, weight_region=region((0.6, 0.7), (0.3, 0.4)))
    ).decision["robustness"]
    assert stable["unique_robust_winners"] == ["A"]
    for bounds in [((0.7, 0.8), (0.7, 0.8)), ((-0.1, 0.5), (0.5, 1.0))]:
        with pytest.raises(PreconditionViolation):
            dispatch(c.job, replace(c, weight_region=region(*bounds)))
    unsupported = replace(region(), relationships=["x+y <= .9"])
    r = dispatch(c.job, replace(c, weight_region=unsupported)).decision["robustness"]
    assert r["execution_status"] == "unsupported"
    with pytest.raises(PreconditionViolation):
        dispatch(
            c.job, replace(c, weight_region=replace(region(), attribute_ranges={}))
        )


def test_joint_change_exposes_missed_one_at_a_time_reversal():
    from dominant_circuit.core.robustness import additive_robustness
    from dominant_circuit import AttributeRange

    attrs = [AttributeRange(n, 0, 1) for n in ["x", "y", "z"]]
    scored = [
        dict(name="A", levels={"x": 1, "y": 0, "z": 0}),
        dict(name="B", levels={"x": 0, "y": 0.48, "z": 0.48}),
    ]
    # Baseline (.34,.33,.33) favors A. Moving .01 from x to either other
    # attribute individually keeps A ahead; moving .02 jointly makes B win.
    assert 0.33 > 0.48 * (0.34 + 0.33)
    assert 0.32 < 0.48 * (0.34 + 0.34)
    domain = WeightRegion(
        {"x": (0.32, 0.34), "y": (0.33, 0.34), "z": (0.33, 0.34)},
        "synthetic",
        "d",
        attribute_ranges={n: (0, 1) for n in ["x", "y", "z"]},
    )
    r = additive_robustness(scored, attrs, domain, "A")
    assert r["action_changed"] and not r["robust_winners"]


def test_ties_and_action_projection_ignore_metadata():
    from dominant_circuit import overturn_test

    c = replace(offers(), scaling_constants={"x": 0.99 / 1.99, "y": 1 / 1.99})
    assert dispatch(c.job, c).decision["tie_set"] == ["A", "B"]
    r = overturn_test(mdp(), "k_max", [{"k_max": 1}])
    assert r.outcome == "stable_within_tested_bounds"
    assert r.comparison_scope == "full_policy"
    assert r.probes[0]["action_changed"] is False


def test_roundtrip_and_adoption_boundary():
    for value in (None, False, 0.0, "indifferent", "not_applicable", {"range": (0, 1)}):
        record = evidence(
            "input",
            value,
            origin="model_proposal",
            acceptance="scenario_only",
            adoption_event=None,
        )
        assert decode(json.loads(json.dumps(encode(record)))) == record
    c = mdp()
    c.provenance = {"gamma": evidence("gamma", 0.9)}
    assert decode(json.loads(json.dumps(encode(c)))) == c
    with pytest.raises(ValueError):
        ConsequentialInput("p", False, acceptance="accepted_for_this_decision")
    with pytest.raises(TypeError):
        encode(lambda: None)


def test_translate_static_paraphrase_and_fact_change():
    desc = DecisionDescription(
        "decision-1", "Compare offers", problem_types=["static_comparison"]
    )
    c = offers()
    for name in (
        "attributes",
        "alternatives",
        "scaling_constants",
        "independence_assumptions",
    ):
        desc.inputs[name] = evidence(name, getattr(c, name))
        desc.translations.append(
            TranslationRecord(
                [name], name, "direct-host-field", "Explicit synthetic input"
            )
        )
    first = translate_decision(desc)
    assert first.status == "translated" and first.contract.horizon is None
    desc.question = "Which offer suits me? I can negotiate."
    assert translate_decision(desc).contract == first.contract
    desc.inputs["scaling_constants"] = evidence(
        "scaling_constants", {"x": 0.49, "y": 0.51}, revision=2
    )
    assert (
        dispatch(Job.MULTIOBJECTIVE, translate_decision(desc).contract).decision[
            "best_alternative"
        ]
        == "B"
    )
    desc.problem_types.append("discounted_mdp")
    assert translate_decision(desc).status == "unsupported_model"
    desc.problem_types = ["static_comparison"]
    desc.translations[0].unresolved_alternatives = ["measurement", "value scale"]
    assert translate_decision(desc).status == "unresolved"


def test_exploration_adoption_revision_and_reopening():
    c = supported(offers())
    report = dispatch(c.job, c)
    assert report.readiness.state == "ready_under_stated_conditions"
    assert "does not authorize" in report.execution_note
    c.provenance["scaling_constants"] = evidence(
        "weights", c.scaling_constants, acceptance="scenario_only"
    )
    assert dispatch(c.job, c).readiness.state == "exploratory"
    session = DecisionSession("decision-1")
    session.revise_preference(
        PreferenceRevision(
            "weights", None, 1, {"x": 0.5, "y": 0.5}, "exploratory_scenario"
        )
    )
    session.revise_preference(
        PreferenceRevision(
            "weights",
            1,
            2,
            {"x": 0.5, "y": 0.5},
            "adopted_for_this_decision",
            "host:adopt",
        )
    )
    session.inputs["unrelated"] = evidence("unrelated", 0)
    session.inputs["derived"] = evidence(
        "derived", 1, origin="derived", dependencies=["weights"]
    )
    session.record_output("ranking", report, ["derived"])
    session.record_output("other", report, ["unrelated"])
    changed = session.revise_preference(
        PreferenceRevision(
            "weights",
            2,
            3,
            {"x": 0.49, "y": 0.51},
            "adopted_for_this_decision",
            "host:revise",
        )
    )
    assert changed == ["ranking"] and session.outputs["ranking"]["stale"]
    assert session.outputs["ranking"]["report"].readiness.state == "blocked"
    assert not session.outputs["other"]["stale"]
    assert session.inputs["derived"].acceptance == "unresolved"
    assert len(session.preferences) == 3 and len(session.history) >= 2
    loaded = decode(json.loads(json.dumps(encode(report))))
    assert loaded.readiness.state == "conditional"


def test_readiness_requires_evidence_and_does_not_promote_proposals():
    c = offers()
    r = dispatch(c.job, c)
    assert r.readiness.state == "conditional" and not r.analysis_is_complete
    c = supported(c)
    c.provenance["attributes"] = replace(
        c.provenance["attributes"], origin="model_proposal"
    )
    assert dispatch(c.job, c).readiness.state == "conditional"
    assert not AuditResult().passed
    d = r.to_dict()
    assert d["readiness"]["state"] in r.to_markdown()
    assert d["execution_note"] == r.execution_note


def test_cardinal_scores_do_not_hide_empty_or_nan():
    from dominant_circuit import Information

    for scores in ([], [float("nan")] * 100, [2.0] * 100):
        with pytest.raises(PreconditionViolation):
            dispatch(
                Job.STOPPING,
                stopping(
                    recall_allowed=False, rejection_prob=0.0, scores=scores
                ).__class__(
                    **{
                        **vars(
                            stopping(
                                recall_allowed=False, rejection_prob=0.0, scores=scores
                            )
                        ),
                        "information": Information.CARDINAL,
                    }
                ),
            )


def test_stopping_nonfinite_parameters_rejected():
    for name, value in [
        ("n", 1.5),
        ("n", float("inf")),
        ("rejection_prob", float("nan")),
    ]:
        c = stopping(recall_allowed=False, rejection_prob=0.0)
        with pytest.raises(PreconditionViolation):
            dispatch(c.job, replace(c, **{name: value}))


def test_explicit_dispatch_does_not_silently_compose_models():
    with pytest.raises(UnclassifiedVariant):
        dispatch(
            Job.MULTIOBJECTIVE,
            replace(offers(), states=["s"], actions=["a"], gamma=0.9),
        )


def test_runner_up_includes_dominated_options_and_zero_weight_ties():
    c = offers()
    c.alternatives = [
        {"name": "A", "x": 0.9, "y": 0.9},
        {"name": "B", "x": 0.8, "y": 0.8},
        {"name": "C", "x": 0.1, "y": 1.0},
    ]
    r = dispatch(c.job, c)
    assert r.decision["runner_up"] == "B"
    assert r.decision["winning_margin"] == pytest.approx(0.1)
    c.alternatives = [
        {"name": "A", "x": 1.0, "y": 1.0},
        {"name": "B", "x": 1.0, "y": 0.0},
    ]
    c.scaling_constants = {"x": 1.0, "y": 0.0}
    assert dispatch(c.job, c).decision["tie_set"] == ["A", "B"]


def test_terminal_model_conflict_is_not_silently_discarded():
    with pytest.raises(PreconditionViolation):
        value_iteration(
            ["end"], ["a"], {("end", "a"): 1.0}, {}, 0.9, terminal_states=["end"]
        )


def test_uncertain_constraint_has_bounded_feasibility():
    constraint = Constraint(
        "pickup", "pickup", "<=", 17, evidence("pickup", 17), "decision-1"
    )
    assert (
        constraint.evaluate(
            {"pickup": {"lower": 15, "upper": 16, "evidence_ref": "host:range"}}
        )
        is True
    )
    assert (
        constraint.evaluate(
            {"pickup": {"lower": 16, "upper": 18, "evidence_ref": "host:range"}}
        )
        is None
    )
    assert (
        constraint.evaluate(
            {"pickup": {"lower": 18, "upper": 19, "evidence_ref": "host:range"}}
        )
        is False
    )


def test_scenario_and_legacy_preserve_provenance_without_inventing_adoption():
    from dominant_circuit import (
        scenario_branch,
        migrate_legacy_contract,
        load_historical_report,
    )

    c = supported(offers())
    branched = scenario_branch(
        c, {"scaling_constants": {"x": 0.49, "y": 0.51}}, "scenario-2"
    )
    assert branched.provenance["scaling_constants"].acceptance == "scenario_only"
    assert c.provenance["scaling_constants"].acceptance == "accepted_for_this_decision"
    assert branched.provenance["scaling_constants"].dependencies == [
        "scaling_constants"
    ]
    legacy = migrate_legacy_contract(
        {"job": "stopping", "recall_allowed": False, "rejection_prob": 0.0}
    )
    assert legacy.recall_allowed is False and legacy.rejection_prob == 0.0
    assert all(
        v.origin == "legacy" and v.acceptance == "unresolved"
        for v in legacy.provenance.values()
    )
    loaded = load_historical_report(
        {"analysis_is_complete": True, "execution_note": "EXECUTE"}
    )
    assert (
        not loaded["analysis_is_complete"]
        and loaded["readiness"]["state"] == "conditional"
    )


def test_end_to_end_example_and_live_gate():
    import runpy
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    example = runpy.run_path(str(root / "examples/reflective_decision.py"))[
        "run_example"
    ]()
    assert example["revised"].decision["best_alternative"] == "B"
    check = runpy.run_path(str(root / "scripts/check_release.py"))["check"]
    cases = json.loads((root / "tests/fixtures/host_release_cases.json").read_text())[
        "cases"
    ]
    assert len(cases) == 6 and all(c["allowed"] and c["forbidden"] for c in cases)
    assert check({}, cases)
    good = dict(
        independent_review={"approved": True},
        live_host=dict(
            model="synthetic-test",
            version="test",
            prompt_sha256="test",
            tool_configuration="test",
            runs=[
                dict(
                    case_id=c["id"],
                    critical_failures=[],
                    human_review=True,
                    structured_states=[{}],
                    unnecessary_questions=0,
                    useful_recovery=True,
                )
                for c in cases
                for _ in range(3)
            ],
        ),
    )
    assert check(good, cases) == []
    good["live_host"]["runs"][0]["critical_failures"] = ["stale recommendation"]
    assert check(good, cases)


def test_adopted_weight_domain_can_make_point_preferences_irrelevant():
    from dominant_circuit import explore_weight_region

    c = supported(offers())
    c.scaling_constants = None
    c.provenance.pop("scaling_constants")
    c.uncertainty_treatment = None
    c.weight_region = replace(
        region((0.6, 0.7), (0.3, 0.4)),
        acceptance="accepted_for_this_decision",
        adoption_event="host:adopt-domain",
    )
    r = explore_weight_region(c)
    assert r.readiness.state == "ready_under_stated_conditions"
    assert (
        r.assumption_support["scaling_constants"]
        == "unknown_but_decision_irrelevant_within_weight_region"
    )
    assert r.decision["best_alternative"] == "A"
    assert r.provenance["scaling_constants"].origin == "model_proposal"
    assert c.scaling_constants is None
