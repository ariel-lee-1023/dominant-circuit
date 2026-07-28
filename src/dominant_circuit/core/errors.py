"""Error taxonomy — Stage 1/2 failures surface as typed exceptions with remedy hints."""

from __future__ import annotations


class DominantCircuitError(Exception):
    """Base. Carries a machine-readable remediation hint for the host AI."""

    def __init__(self, message: str, *, remedy: str = "", field: str = ""):
        super().__init__(message)
        self.remedy = remedy
        self.field = field


class ContractIncomplete(DominantCircuitError):
    """Stage 1 failure. .field names the first missing field; .remedy is the question to ask."""


class PreconditionViolation(DominantCircuitError):
    """Stage 2 failure. A mathematical law is violated. Do not compute."""


class NoOptimalStoppingRuleExists(PreconditionViolation):
    """Diverging expected payoff — no stopping rule exists. Switch to bankroll-fraction framework."""


class IndependenceNotVerified(PreconditionViolation):
    """Additive/multiplicative form forbidden until flip-test (or equivalent) is recorded."""


class NonMarkovProcess(PreconditionViolation):
    """Sequential methods require the Markov property; augment the state or refuse."""


class UnclassifiedVariant(DominantCircuitError):
    """Assumption combination is absent from the corpus Decision Table. Do not invent a constant."""


class AuditFailure(DominantCircuitError):
    """A validation invariant failed. Do not return the decision; loop back to Stage 1.

    Carries enough to loop back to the *right* question rather than starting over:
      .invariants — the InvariantResult objects that failed, each with its message
      .invariant_ids — their IDs, e.g. ['INV-1', 'INV-3']
      .fields — the contract fields implicated, i.e. what to re-elicit
      .field — the first of those, matching the base-class convention
    """

    def __init__(self, message: str, *, remedy: str = "", field: str = "",
                 invariants: list | None = None, fields: list[str] | None = None):
        self.invariants = list(invariants or [])
        self.invariant_ids = [r.invariant_id for r in self.invariants]
        self.fields = list(fields or [])
        super().__init__(message, remedy=remedy, field=field or (self.fields[0] if self.fields else ""))


class NotInCorpus(DominantCircuitError):
    """Required cluster file or section citation does not resolve."""
