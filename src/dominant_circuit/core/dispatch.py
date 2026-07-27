"""Stage 3 orchestrator — verify → compute → audit → report. No I/O."""

from __future__ import annotations

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
    require_audit_pass(report.audit)

    return report
