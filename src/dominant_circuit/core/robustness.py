"""Bounded additive sensitivity on a box intersected with the weight simplex.

For each pair, minimize the linear score difference by filling the cheapest
coefficient first after assigning lower bounds. This solves this particular
linear program globally; arbitrary extra inequalities are explicitly unsupported.
"""

from dataclasses import dataclass, field
from itertools import combinations
import math
from .errors import PreconditionViolation


@dataclass
class WeightRegion:
    bounds: dict[str, tuple[float, float]]
    evidence_ref: str
    scope: str
    acceptance: str = "scenario_only"
    attribute_ranges: dict = field(default_factory=dict)
    relationships: list = field(default_factory=list)
    schema_version: int = 2
    adoption_event: str | None = None

    def __post_init__(self):
        if self.acceptance not in {
            "scenario_only",
            "accepted_for_this_decision",
            "unresolved",
            "rejected",
        }:
            raise ValueError("Unknown domain acceptance")
        if self.acceptance == "accepted_for_this_decision" and not self.adoption_event:
            raise ValueError("Domain adoption requires an identifiable host event")


def comparison_summary(scored, attributes, weights, tolerance=1e-9):
    ranked = sorted(scored, key=lambda s: -s["utility"])
    if not ranked:
        return dict(
            runner_up=None,
            winning_margin=None,
            tie_set=[],
            tie_tolerance=tolerance,
            switching_boundaries=[],
        )
    best = ranked[0]["utility"]
    boundaries = []
    if len(attributes) == 2 and abs(sum(weights.values()) - 1) <= tolerance:
        from ..engines.multiobjective import _normalize

        x, y = attributes
        for a, b in combinations(ranked, 2):
            dx = _normalize(a["levels"][x.name], x) - _normalize(b["levels"][x.name], x)
            dy = _normalize(a["levels"][y.name], y) - _normalize(b["levels"][y.name], y)
            if abs(dx - dy) > tolerance:
                w = -dy / (dx - dy)
                if 0 <= w <= 1:
                    boundaries.append(
                        dict(
                            alternatives=[a["name"], b["name"]],
                            attribute=x.name,
                            weight=w,
                            dependent_weight={y.name: 1 - w},
                            method="analytic_pairwise_tie",
                        )
                    )
    return dict(
        runner_up=ranked[1]["name"] if len(ranked) > 1 else None,
        winning_margin=best - ranked[1]["utility"] if len(ranked) > 1 else None,
        tie_set=[r["name"] for r in ranked if best - r["utility"] <= tolerance],
        tie_tolerance=tolerance,
        switching_boundaries=boundaries,
    )


def additive_robustness(scored, attributes, region, baseline, tolerance=1e-9):
    from ..engines.multiobjective import _normalize

    names = [a.name for a in attributes]
    if set(region.bounds) != set(names) or not region.evidence_ref or not region.scope:
        raise PreconditionViolation(
            "Weight region needs all attributes, source and scope",
            field="weight_region",
        )
    expected_ranges = {a.name: (a.worst, a.best) for a in attributes}
    if region.attribute_ranges != expected_ranges:
        raise PreconditionViolation(
            "Weight assessment ranges changed or were not recorded; reassess weights",
            field="weight_region",
        )
    if region.relationships:
        return dict(
            outcome="untested",
            execution_status="unsupported",
            method="none",
            coverage="none",
            limitation="Only bound constraints and sum(weights)=1 are implemented",
        )
    for lo, hi in region.bounds.values():
        if not all(math.isfinite(v) for v in (lo, hi)) or not 0 <= lo <= hi <= 1:
            raise PreconditionViolation("Invalid weight bounds", field="weight_region")
    if (
        sum(v[0] for v in region.bounds.values()) > 1 + tolerance
        or sum(v[1] for v in region.bounds.values()) < 1 - tolerance
    ):
        raise PreconditionViolation(
            "Empty normalized weight region", field="weight_region"
        )
    values = {
        r["name"]: {a.name: _normalize(r["levels"][a.name], a) for a in attributes}
        for r in scored
    }
    certificates = []
    for candidate in values:
        for rival in values:
            if candidate == rival:
                continue
            coeff = {n: values[candidate][n] - values[rival][n] for n in names}
            witness = {n: region.bounds[n][0] for n in names}
            remaining = 1 - sum(witness.values())
            for name in sorted(names, key=lambda n: coeff[n]):
                amount = min(remaining, region.bounds[name][1] - witness[name])
                witness[name] += amount
                remaining -= amount
            margin = sum(witness[n] * coeff[n] for n in names)
            certificates.append(
                dict(
                    candidate=candidate,
                    rival=rival,
                    minimum_margin=margin,
                    witness=witness,
                )
            )
    robust = [
        name
        for name in values
        if all(
            c["minimum_margin"] >= -tolerance
            for c in certificates
            if c["candidate"] == name
        )
    ]
    unique = [
        name
        for name in values
        if all(
            c["minimum_margin"] > tolerance
            for c in certificates
            if c["candidate"] == name
        )
    ]
    baseline_can_lose = any(
        c["minimum_margin"] < -tolerance
        for c in certificates
        if c["candidate"] == baseline
    )
    return dict(
        schema_version=2,
        outcome=(
            "changes_decision" if baseline_can_lose else "stable_within_tested_bounds"
        ),
        execution_status="completed",
        method="linear_program_box_simplex_greedy",
        coverage="whole_domain",
        domain=region.bounds,
        evidence_ref=region.evidence_ref,
        acceptance=region.acceptance,
        scope=region.scope,
        baseline=baseline,
        robust_winners=robust,
        unique_robust_winners=unique,
        pairwise_certificates=certificates,
        model_changed=False,
        action_changed=baseline_can_lose,
        feasibility_changed=False,
        limitations=[
            "Fixed attribute values and ranges; ties within tolerance",
            "No regret interpretation without an adopted cardinal value scale",
        ],
    )


def explore_weight_region(contract):
    """Explore a supplied region without eliciting a premature point preference.

    The deterministic anchor is labelled as a proposed computational scenario;
    any whole-domain conclusion derives from pairwise optimization over the region.
    """
    from .evidence import scenario_branch
    from .dispatch import dispatch

    region = contract.weight_region
    if region is None:
        raise PreconditionViolation(
            "Supply a sourced weight region", field="weight_region"
        )
    anchor = {name: bounds[0] for name, bounds in region.bounds.items()}
    remaining = 1 - sum(anchor.values())
    for name in sorted(anchor):
        amount = min(max(remaining, 0.0), region.bounds[name][1] - anchor[name])
        anchor[name] += amount
        remaining -= amount
    branch = scenario_branch(
        contract, {"scaling_constants": anchor}, "weight-region-anchor"
    )
    report = dispatch(contract.job, branch)
    report.decision["scenario_anchor"] = dict(
        weights=anchor,
        origin="model_proposal",
        purpose="Computational anchor only; whole-domain robustness determines preference irrelevance",
    )
    return report
