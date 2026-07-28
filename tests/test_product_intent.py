"""The four product-intent tests from SPEC.md §15.7.

These are the claims the product exists to make good on. All four must pass —
in particular all four, not three. Before T2, the fourth could not pass at all:
INV-1 was emitted as a hardcoded `True`, so no invariant could ever fail and
`AuditFailure` was unreachable from a returned report.
"""

import pytest

from dominant_circuit import (
    AuditFailure, AuditResult, ContractIncomplete, Horizon, Information,
    InputContract, InvariantResult, Job, NoOptimalStoppingRuleExists, Payoff,
    QUESTION_BANK, UnclassifiedVariant, dispatch,
)
from dominant_circuit.core.audit import require_audit_pass
from dominant_circuit.engines.stopping import CALIBRATIONS, check_assumption_set_match


def test_incomplete_contract_cannot_yield_a_number():
    """An incomplete contract cannot yield a number: ContractIncomplete names the
    missing field and supplies the question to ask."""
    contract = InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=10,
                             information=Information.ORDINAL,
                             payoff=Payoff.BEST_OR_NOTHING)
                             # payoff_diverges deliberately never elicited

    with pytest.raises(ContractIncomplete) as ei:
        dispatch(Job.STOPPING, contract)

    assert ei.value.field == "payoff_diverges"
    assert ei.value.remedy == QUESTION_BANK["payoff_diverges"]
    assert ei.value.remedy.strip().endswith("?"), "remedy must be an askable question"


def test_diverging_payoff_yields_a_refusal_never_an_answer():
    """payoff_diverges=True yields NoOptimalStoppingRuleExists, never an answer."""
    contract = InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=10,
                             information=Information.ORDINAL,
                             payoff=Payoff.BEST_OR_NOTHING, payoff_diverges=True)

    with pytest.raises(NoOptimalStoppingRuleExists) as ei:
        dispatch(Job.STOPPING, contract)

    # the refusal must point somewhere useful, not just say no
    assert "Kelly" in ei.value.remedy or "bankroll" in ei.value.remedy


def test_uncalibrated_recall_probability_refuses_rather_than_reusing_061():
    """Changing recall_accept_prob from 0.5 to 0.3 changes the output — to a
    refusal — rather than silently reusing the 0.61 constant."""
    def contract(prob):
        return InputContract(
            job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
            information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
            payoff_diverges=False, recall_allowed=True, recall_accept_prob=prob,
        )

    calibrated = dispatch(Job.STOPPING, contract(0.5))
    assert calibrated.numeric["r_star"] == 61

    with pytest.raises(UnclassifiedVariant) as ei:
        dispatch(Job.STOPPING, contract(0.3))
    assert "0.61" in str(ei.value)


def test_failed_invariant_raises_and_is_never_buried_in_a_returned_report():
    """A failed invariant raises AuditFailure and is never buried inside a
    returned report.

    Built from the real check, not a stub: the 0.61 recall calibration is handed
    a contract that elicited no recall, which is exactly the contradiction INV-1
    exists to catch.
    """
    contract = InputContract(
        job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
        information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
        payoff_diverges=False, recall_allowed=False,
    )
    inv1 = check_assumption_set_match(contract, CALIBRATIONS["recall_61"])
    assert inv1.passed is False, "INV-1 must be a real check, not a literal"

    with pytest.raises(AuditFailure) as ei:
        require_audit_pass(AuditResult(results=[inv1]))
    assert "INV-1" in str(ei.value)


def test_dispatch_never_returns_a_report_whose_audit_failed():
    """The pipeline-level version of the same claim: whatever dispatch returns,
    its audit passed. A failing audit leaves by exception."""
    contracts = [
        InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
                      information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
                      payoff_diverges=False),
        InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=100,
                      information=Information.ORDINAL, payoff=Payoff.BEST_OR_NOTHING,
                      payoff_diverges=False, recall_allowed=True, recall_accept_prob=0.5),
        InputContract(job=Job.STOPPING, horizon=Horizon.FIXED_KNOWN, n=40,
                      information=Information.CARDINAL, payoff=Payoff.BEST_OR_NOTHING,
                      payoff_diverges=False),
    ]
    for contract in contracts:
        report = dispatch(Job.STOPPING, contract)
        assert report.audit.passed
        assert report.audit.failures == []
        assert report.audit.results, "a report with no invariants is not audited"
