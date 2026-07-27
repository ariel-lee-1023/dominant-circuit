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
    """A validation invariant failed. Do not return the decision; loop back to Stage 1."""


class NotInCorpus(DominantCircuitError):
    """Required cluster file or section citation does not resolve."""
