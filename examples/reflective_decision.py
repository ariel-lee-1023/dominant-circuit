"""Synthetic host events: explore, adopt, compare, revise and reopen. No real users."""

from dataclasses import fields, replace
from dominant_circuit import (
    InputContract,
    Job,
    AttributeRange,
    record_independence,
    ConsequentialInput,
    Constraint,
    DecisionSession,
    PreferenceRevision,
    WeightRegion,
    dispatch,
    scenario_branch,
)
from dominant_circuit.core.readiness import COMPUTATIONAL_FIELDS


def host_record(name, value, event="synthetic:adopt"):
    return ConsequentialInput(
        name,
        value,
        origin="user_report",
        evidence_ref=event,
        acceptance="accepted_for_this_decision",
        scope="offers",
        adoption_event=event,
    )


def run_example():
    contract = InputContract(
        job=Job.MULTIOBJECTIVE,
        decision_id="offers",
        alternatives=[
            {"name": "A", "salary": 1.0, "commute": 0.0, "pickup": 18},
            {"name": "B", "salary": 0.0, "commute": 0.99, "pickup": 16},
        ],
        attributes=[AttributeRange("salary", 0, 1), AttributeRange("commute", 0, 1)],
        scaling_constants={"salary": 0.5, "commute": 0.5},
        independence_assumptions=[
            record_independence(
                {a},
                {b},
                "preferential",
                True,
                evidence="Synthetic independence assumption",
            )
            for a, b in [("salary", "commute"), ("commute", "salary")]
        ],
    )
    scenario = scenario_branch(
        contract, {"scaling_constants": {"salary": 0.5, "commute": 0.5}}, "explore"
    )
    explored = dispatch(Job.MULTIOBJECTIVE, scenario)
    assert explored.readiness.state == "exploratory"

    session = DecisionSession("offers")
    session.revise_preference(
        PreferenceRevision(
            "scaling_constants",
            None,
            1,
            contract.scaling_constants,
            "exploratory_scenario",
        )
    )
    session.revise_preference(
        PreferenceRevision(
            "scaling_constants",
            1,
            2,
            contract.scaling_constants,
            "adopted_for_this_decision",
            "synthetic:adopt",
        )
    )
    contract.provenance = {
        f.name: host_record(f.name, getattr(contract, f.name))
        for f in fields(contract)
        if f.name not in COMPUTATIONAL_FIELDS and getattr(contract, f.name) is not None
    }
    contract.provenance["scaling_constants"] = session.inputs["scaling_constants"]
    contract.weight_region = WeightRegion(
        {"salary": (0.49, 0.51), "commute": (0.49, 0.51)},
        "synthetic:plausible-range",
        "offers",
        attribute_ranges={"salary": (0, 1), "commute": (0, 1)},
    )
    conditional = dispatch(Job.MULTIOBJECTIVE, contract)
    assert conditional.decision["robustness"]["action_changed"]
    assert conditional.readiness.state == "conditional"
    session.record_output("ranking", conditional, ["scaling_constants"])

    session.revise_preference(
        PreferenceRevision(
            "scaling_constants",
            2,
            3,
            {"salary": 0.49, "commute": 0.51},
            "adopted_for_this_decision",
            "synthetic:revision",
            reason="A concrete schedule made commute more valuable for this decision.",
        )
    )
    assert session.outputs["ranking"]["stale"]
    contract = replace(
        contract,
        revision=2,
        scaling_constants=session.inputs["scaling_constants"].value,
    )
    contract.provenance["scaling_constants"] = session.inputs["scaling_constants"]
    contract.constraints = [
        Constraint("pickup", "pickup", "<=", 17, host_record("pickup", 17), "offers")
    ]
    contract.uncertainty_treatment = host_record(
        "deadline-choice",
        "Decide under the stated residual uncertainty before the offer deadline; reopen if pickup changes.",
    )
    revised = dispatch(Job.MULTIOBJECTIVE, contract)
    assert revised.decision["best_alternative"] == "B"
    assert revised.readiness.state == "ready_under_stated_conditions"
    return dict(
        exploration=explored, conditional=conditional, revised=revised, session=session
    )


if __name__ == "__main__":
    result = run_example()
    for stage in ("exploration", "conditional", "revised"):
        print(stage)
        print(result[stage].to_markdown())
