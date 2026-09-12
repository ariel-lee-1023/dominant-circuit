"""Readiness policy: computational evidence is necessary but never sufficient."""

from dataclasses import fields
from copy import deepcopy
from .contract import Job
from .evidence import ConsequentialInput
from .report import ReadinessAssessment

COMPUTATIONAL_FIELDS = {
    "schema_version",
    "investigation_id",
    "investigation_handoff_ref",
    "decision_id",
    "revision",
    "provenance",
    "job",
    "k_max",
    "tolerance",
    "exact_finite_n",
    "mcts_simulations",
    "search_depth",
    "independence_tests",
    "weight_region",
    "uncertainty_treatment",
    "constraints",
}


def required_checks(job, report):
    if job == Job.STOPPING:
        return ["INV-1", "INV-6"]
    if job == Job.MULTIOBJECTIVE:
        return ["INV-3", "INV-5"]
    if "belief" in report.decision:
        return ["INV-2"]
    return ["INV-4", "INV-markov"]


def assess_readiness(contract, report):
    reasons, support, supporting = [], {}, []
    required = [
        f.name
        for f in fields(contract)
        if f.name not in COMPUTATIONAL_FIELDS
        and getattr(contract, f.name) is not None
        and getattr(contract, f.name) != []
    ]
    ids = {
        v.input_id: v
        for v in contract.provenance.values()
        if isinstance(v, ConsequentialInput)
    }

    def accepted(record, seen=None):
        seen = set() if seen is None else seen
        if not isinstance(record, ConsequentialInput) or record.input_id in seen:
            return False
        seen = seen | {record.input_id}
        if (
            record.acceptance != "accepted_for_this_decision"
            or record.scope != contract.decision_id
            or not record.evidence_ref
            or not record.adoption_event
        ):
            return False
        if record.origin in {"legacy", "model_proposal"}:
            return False
        return all(
            dep in ids and accepted(ids[dep], seen) for dep in record.dependencies
        )

    d = report.decision if isinstance(report.decision, dict) else {}
    termination = d.get("termination_reason", "completed")
    if termination != "completed" and termination != "converged":
        reasons.append(f"Computation terminated: {termination}")
    feasibility = d.get("feasibility_status", "assumed_under_model")
    if feasibility in {"unknown", "empty"}:
        reasons.append(f"Feasibility is {feasibility}")
    robustness = d.get("robustness", {})
    treatment = contract.uncertainty_treatment
    scoped_treatment = accepted(treatment) and bool(treatment.value)
    domain = contract.weight_region
    robust = (
        robustness.get("coverage") == "whole_domain"
        and d.get("best_alternative") in robustness.get("unique_robust_winners", [])
        and domain is not None
        and domain.acceptance == "accepted_for_this_decision"
        and domain.scope == contract.decision_id
        and domain.adoption_event
    )
    for name in required:
        if name == "scaling_constants" and robust:
            support[name] = "unknown_but_decision_irrelevant_within_weight_region"
            supporting.append(domain.evidence_ref)
            continue
        record = contract.provenance.get(name)
        good = accepted(record) and record.value == getattr(contract, name)
        support[name] = "accepted_scoped_input" if good else "unresolved_or_scenario"
        if good:
            supporting.append(record.input_id)
        else:
            reasons.append(f"Input support unresolved or scenario-only: {name}")
    for constraint in contract.constraints:
        if (
            not accepted(constraint.provenance)
            or constraint.scope != contract.decision_id
            or constraint.provenance.value != constraint.limit
        ):
            reasons.append(f"Constraint support unresolved: {constraint.constraint_id}")
    if not scoped_treatment and not robust:
        reasons.append(
            "Consequential uncertainty has no adopted treatment or supported whole-domain certificate"
        )
    if "belief" in d:
        reasons.append("Belief estimation provides no action-planning capability")
    if not report.audit.passed:
        reasons.append(
            "Mandatory audit checks failed or are missing: "
            + ", ".join(report.audit.missing_checks)
        )
    scenarios = any(
        isinstance(v, ConsequentialInput) and v.acceptance == "scenario_only"
        for v in contract.provenance.values()
    )
    state = "exploratory" if scenarios else "conditional"
    if not reasons:
        state = "ready_under_stated_conditions"
    if (
        not report.audit.passed
        or feasibility == "empty"
        or (contract.job == Job.MULTIOBJECTIVE and not d.get("best_alternative"))
        or termination == "numerical_failure"
    ):
        state = "blocked"
    report.contract_revision = contract.revision
    report.provenance = deepcopy(contract.provenance)
    for constraint in contract.constraints:
        report.provenance[f"constraint:{constraint.constraint_id}"] = deepcopy(
            constraint.provenance
        )
        supporting.append(constraint.provenance.input_id)
    if treatment is not None:
        report.provenance["uncertainty_treatment"] = deepcopy(treatment)
        supporting.append(treatment.input_id)
    if domain is not None:
        report.provenance["weight_region"] = deepcopy(domain)
        supporting.append(domain.evidence_ref)
    report.assumption_support = support
    report.computation = dict(
        engine=contract.job.value,
        model_version=2,
        contract_revision=contract.revision,
        termination_reason=termination,
        method=d.get("method", report.formula_name),
        criterion=d.get("criterion"),
        residual=d.get("final_residual"),
        value_error_bound=d.get("value_error_bound"),
        requested_tolerance=contract.tolerance,
        dependencies=supporting,
    )
    report.readiness = ReadinessAssessment(
        state=state,
        supporting_records=supporting,
        reasons=reasons
        or ["Supported computation and scoped inputs under the recorded conditions."],
        remaining_uncertainty=(
            []
            if robust
            else [
                "Residual uncertainty retained; adoption does not establish empirical truth."
            ]
        ),
        conditions_of_use=[
            f"Decision {contract.decision_id}, revision {contract.revision}",
            "Model assumptions and feasibility remain valid",
            (
                str(treatment.value)
                if scoped_treatment
                else "Sensitivity is limited to the stated domain"
            ),
        ],
        next_observations=reasons.copy(),
        completed_checks=[r.invariant_id for r in report.audit.results if r.passed],
    )
    if state != "ready_under_stated_conditions":
        if contract.job == Job.STOPPING:
            report.action = f"Conditional model result: {report.decision}. Interpret only under the stated assumptions and readiness conditions."
        else:
            report.action = f"{state.capitalize()} model result. " + report.action
    return report
