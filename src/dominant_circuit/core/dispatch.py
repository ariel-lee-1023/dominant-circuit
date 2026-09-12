"""Stage 3 orchestrator — verify → compute → audit → report. No I/O."""

from __future__ import annotations
from copy import deepcopy
from .readiness import assess_readiness, required_checks
from .report import InvariantResult

from ..core.contract import InputContract, Job
from ..core.verify import verify_preconditions
from ..core.audit import run_validation_invariants, require_audit_pass
from ..core.report import OutputReport
from ..engines.stopping import solve_stopping
from ..engines.multiobjective import solve_multiobjective
from ..engines.sequential import solve_sequential


def dispatch(job: Job | str, contract: InputContract, **kwargs) -> OutputReport:
    if isinstance(job, str):
        job = Job(job.lower().strip())
    investigation = kwargs.get("investigation")
    if contract.investigation_id is not None:
        if investigation is None:
            raise ValueError(
                "A bound Stage 0 handoff requires the current investigation state"
            )
        if contract.job != job:
            raise ValueError("The requested engine differs from the bound handoff")
        investigation.validate_handoff(contract)
    contract = deepcopy(contract)
    contract.job = job

    verify_preconditions(contract)

    if job == Job.STOPPING:
        report = solve_stopping(contract)
    elif job == Job.MULTIOBJECTIVE:
        report = solve_multiobjective(contract)
    elif job == Job.SEQUENTIAL:
        report = solve_sequential(contract)
    else:
        raise ValueError(f"Unknown job: {job}")

    if report.audit is None or len(report.audit.results) == 0:
        report.audit = run_validation_invariants(job, contract, report.decision, kwargs)
    report.audit.required_check_ids = required_checks(job, report)
    if job == Job.STOPPING and not any(
        r.invariant_id == "INV-6" for r in report.audit.results
    ):
        report.audit.results.append(
            InvariantResult(
                "INV-6",
                "finite_expectation",
                contract.payoff_diverges is False,
                message="Explicit finite-payoff assumption recorded; empirical support assessed separately",
            )
        )
    require_audit_pass(report.audit)
    assess_readiness(contract, report)

    if contract.investigation_id is not None:
        report.computation["investigation_id"] = contract.investigation_id
        report.computation["investigation_handoff_ref"] = (
            contract.investigation_handoff_ref
        )
        report.readiness.reopening_triggers.append(
            "Investigation evidence, boundary or goal changed: return to Stage 0."
        )
    return report
