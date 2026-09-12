"""Synthetic support-queue investigation plus a direct static comparison."""

from dataclasses import replace
from dominant_circuit import (
    Investigation,
    DecisionDescription,
    WorkingAccount,
    Boundary,
    ObservationPlan,
    PossibleFinding,
    Observation,
    ConsequentialInput,
    AnalyticalResult,
    InputContract,
    Job,
    AttributeRange,
    record_independence,
    dispatch,
)


def evidence(name, value, participant="employee"):
    return ConsequentialInput(
        name,
        value,
        origin="user_report",
        evidence_ref=f"synthetic:{participant}:{name}",
        scope="queue",
    )


def support_queue():
    i = Investigation.begin(
        "queue",
        DecisionDescription(
            "queue",
            "Why did the queue slow despite hiring?",
            objectives=["understand delays"],
        ),
        "synthetic:user-purpose",
    )
    account = WorkingAccount(
        "Capacity and training",
        ("arrivals", "processing time"),
        Boundary(
            ("staffing", "training"),
            ("product defects",),
            ("repeat demand",),
            "Unresolved defects may create demand invisible in handling-time averages.",
            visible_observations=("training time", "handling time"),
            outside_observation="Inspect recurring issue and reopen reasons",
            outside_access="unknown",
        ),
        ("Training temporarily reduces available processing capacity",),
        proposed_by="host",
    )
    return i.propose_account("capacity", account, "synthetic:initial-proposal")


def ticket_plan(i, access="available", accounts=None):
    return ObservationPlan(
        "Compare repeat contacts with training periods",
        "discriminating",
        tuple(accounts or (i.current_model_ref,)),
        ("capacity constraints", "recurring demand"),
        "authorized ticket sample",
        "Read issue and reopening tags alongside training dates",
        (
            PossibleFinding(
                "repeat",
                "Repeated contacts for unresolved defects",
                "Expand demand boundary; capacity may coexist",
            ),
            PossibleFinding(
                "training",
                "Delays concentrated in training periods",
                "Capacity remains plausible within this sample",
            ),
            PossibleFinding(
                "both",
                "Both patterns occur",
                "Retain both mechanisms; contributions remain unknown",
            ),
            PossibleFinding(
                "inconclusive",
                "Both accounts fit or records are incomplete",
                "Describe accessible episodes; pause inaccessible comparisons",
            ),
        ),
        access=access,
        effort_assessment="manageable",
        owner="team analyst",
        effort="small manual sample",
        delay="when accessible",
        collection_effects="Tagging may affect future reporting",
        omission_challenge="Look at recurring issue causes outside handling-time metrics",
    )


def record_episode(
    i, name, text, plan_name="tickets", participant="employee", missingness=()
):
    return i.receive_observation(
        name,
        Observation(
            evidence(name, text, participant),
            "Support tickets during the sampled period",
            missingness=missingness,
            selection_limits=("Convenience sample; no causal identification",),
            raw_episode_ref=f"synthetic:episode:{name}",
            plan_ref=i.latest_ref("plan", plan_name),
            reported_by=participant,
        ),
    )


def expand_demand(i, obs_name="defects"):
    old = i.get(i.current_model_ref)
    combined = replace(
        old,
        name="Capacity and recurring demand",
        boundary=Boundary(
            ("staffing", "training", "recurring product defects"),
            (),
            ("relative contributions", "tagging bias"),
            "The sample may omit people who stopped contacting support.",
            outside_observation="Review available descriptions of unresolved issues",
            outside_access="available",
        ),
        mechanisms=(
            "Training may reduce processing capacity",
            "Unresolved defects may generate repeat contacts",
        ),
        assessment="unassessed",
        assessment_scope="",
        working_use_event=None,
    )
    return i.revise_account(
        "capacity",
        combined,
        ("boundary_revision", "mechanism_revision"),
        i.latest_ref("obs", obs_name),
        "Repeated contacts are not explained by capacity alone; keep both mechanisms possible.",
    )


def offer_contract():
    return InputContract(
        job=Job.MULTIOBJECTIVE,
        attributes=[AttributeRange("pay", 0, 1), AttributeRange("commute", 0, 1)],
        scaling_constants={"pay": 0.5, "commute": 0.5},
        independence_assumptions=[
            record_independence(
                {a}, {b}, "preferential", True, evidence="synthetic scoped assumption"
            )
            for a, b in [("pay", "commute"), ("commute", "pay")]
        ],
        alternatives=[
            {"name": "A", "pay": 1.0, "commute": 0.8},
            {"name": "B", "pay": 0.7, "commute": 0.9},
        ],
    )


def simple_comparison():
    i = Investigation.begin(
        "offers",
        DecisionDescription(
            "offers", "Compare two current offers", problem_types=["static_comparison"]
        ),
        "synthetic:scoped-purpose",
    )
    i = i.handoff("offers", offer_contract())
    c = i.get_handoff("offers")
    report = dispatch(c.job, c, investigation=i)
    return i.record_report("comparison", report, "offers", "synthetic:computed-result")


def run_example():
    initial = support_queue()
    planned = initial.propose_observation(
        "tickets", ticket_plan(initial), "synthetic:plan"
    )
    analyzed = planned.record_analysis(
        "capacity-only",
        AnalyticalResult(
            "queue delays",
            "qualitative capacity account",
            "relevant",
            "Capacity is a provisional contributor",
            limitations=("Product demand not represented",),
        ),
        (planned.current_model_ref,),
        "synthetic:analysis",
    )
    old_result = analyzed.latest_ref("analysis", "capacity-only")
    awaiting = analyzed.await_observation(
        "tickets", "authorized manager", "synthetic:collection-authorization"
    )
    returned = record_episode(
        awaiting,
        "defects",
        "Several people repeatedly contacted support about unresolved defects.",
    )
    assert not returned.is_valid(old_result)
    reviewed = returned.review_observation(
        "defects",
        "repeat",
        {"capacity": "weakened"},
        ("boundary_revision", "mechanism_revision"),
        "A capacity-only account leaves repeat demand unexplained.",
        "synthetic:review",
    )
    revised = expand_demand(reviewed)
    next_step = revised.propose_observation(
        "issue-reasons", ticket_plan(revised), "synthetic:next-observation"
    )
    assert next_step.workflow == "ready_to_observe"
    assert next_step.get(next_step.current_model_ref).assessment == "unassessed"
    simple = simple_comparison()
    assert (
        not simple.accounts
        and simple.get_report("comparison").decision["best_alternative"] == "A"
    )
    return dict(
        initial=initial,
        planned=planned,
        returned=returned,
        reviewed=reviewed,
        revised=next_step,
        simple=simple,
    )


if __name__ == "__main__":
    for stage, state in run_example().items():
        print(stage)
        print(state.to_markdown())
        print()
