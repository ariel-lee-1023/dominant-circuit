"""Output Contract — six mandatory fields."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from enum import Enum
import math


def json_presentation(value):
    """Presentation JSON; use evidence.encode for lossless archival serialization."""
    if isinstance(value,Enum): return value.value
    if isinstance(value,dict): return {str(k):json_presentation(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,set,frozenset)): return [json_presentation(v) for v in value]
    if isinstance(value,float) and not math.isfinite(value): return None
    return value


@dataclass
class InvariantResult:
    invariant_id: str
    name: str
    passed: bool
    residual: Optional[float] = None
    tolerance: Optional[float] = None
    message: str = ""


@dataclass
class AuditResult:
    results: list[InvariantResult] = field(default_factory=list)
    required_check_ids: list[str] = field(default_factory=list)
    not_applicable: dict[str, str] = field(default_factory=dict)

    @property
    def missing_checks(self):
        completed = {r.invariant_id for r in self.results}
        return [name for name in self.required_check_ids if name not in completed
                and not self.not_applicable.get(name)]

    @property
    def passed(self) -> bool:
        return bool(self.results) and not self.missing_checks and not self.failures

    @property
    def failures(self) -> list[InvariantResult]:
        return [r for r in self.results if not r.passed and r.invariant_id != "INV-7"]


@dataclass
class SensitivityEntry:
    assumption: str
    perturbation: str
    new_decision: Any
    decision_changed: bool
    fragility: str


# Orders in the zero-order expansion. These are not severity labels; they are
# structural claims about how a term relates to the trunk.
ORDER_ZERO = "zero"          # the trunk itself
ORDER_FIRST = "first"        # Same model; the recommended action may change.
ORDER_OVERTURN = "overturn"  # a DIFFERENT trunk, not a correction
ORDER_HARD = "hard"          # no trunk exists; veto
ORDER_DROPPED = "dropped"    # thrown away as non-dominant

_ORDER_GLOSS = {
    ORDER_ZERO: "zero-order · trunk",
    ORDER_FIRST: "first-order · same model; action may change",
    ORDER_OVERTURN: "overturn · different zero-order model",
    ORDER_HARD: "hard constraint · no zero-order exists",
    ORDER_DROPPED: "dropped · removed by dominance under stated assumptions",
}


@dataclass
class PerturbationTerm:
    """One term in the zero-order expansion of a decision.

    The distinction that matters is `first` vs `overturn`, and it is decided
    structurally, not by a magnitude threshold: a term is a *correction* when it
    refines the same underlying model, and an *overturn* when it moves the problem
    to a different calibrated model — a different row of the corpus decision table.
    A 65% shift that stays in one model is still a correction; a 5% shift that
    changes models is still an overturn.

    `relative_shift` is the SIGNED (value - zero_order) / |zero_order| where the two
    are numerically comparable, and None otherwise. It is reported for judgement,
    never used for classification.
    """
    order: str                              # ORDER_ZERO | ORDER_FIRST | ORDER_OVERTURN | ORDER_HARD
    label: str
    value: Any
    citation: str
    relative_shift: Optional[float] = None
    note: str = ""

    @property
    def gloss(self) -> str:
        return _ORDER_GLOSS.get(self.order, self.order)


def relative_shift(value: Any, zero_order: Any) -> Optional[float]:
    """Signed (value - base) / |base|, when both are real and the base is non-zero.

    Signed, so a term that moves the decision *down* reads as negative rather than
    as an indistinguishable magnitude.
    """
    try:
        base = float(zero_order)
        if base == 0.0:
            return None
        return (float(value) - base) / abs(base)
    except (TypeError, ValueError):
        return None


@dataclass
class ReadinessAssessment:
    state: str = "exploratory"
    policy_version: int = 2
    supporting_records: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=lambda: ["Assumption support and uncertainty treatment have not been assessed."])
    remaining_uncertainty: list[str] = field(default_factory=list)
    conditions_of_use: list[str] = field(default_factory=list)
    next_observations: list[str] = field(default_factory=list)
    reopening_triggers: list[str] = field(default_factory=lambda: ["Input or preference revision", "Changed deadline", "Violated model or feasibility condition"])
    completed_checks: list[str] = field(default_factory=list)


@dataclass
class OutputReport:
    decision: Any
    formula_name: str
    formula_latex: str
    citation: str
    numeric: dict[str, float]
    assumptions: dict[str, Any]
    sensitivity: list[SensitivityEntry]
    audit: AuditResult
    # Stage 5: the decision restated as an instruction the user can carry out.
    # `decision` is the machine-readable form; this is the executable one.
    action: str = ""
    schema_version: int = 2
    contract_revision: int = 1
    provenance: dict = field(default_factory=dict)
    computation: dict = field(default_factory=dict)
    assumption_support: dict = field(default_factory=dict)
    readiness: ReadinessAssessment = field(default_factory=ReadinessAssessment)
    # The answer as a zero-order expansion: trunk, corrections, overturns, vetoes.
    perturbation: list[PerturbationTerm] = field(default_factory=list)

    def __post_init__(self):
        self._sync_audit_status()

    def _sync_audit_status(self):
        if not self.audit.passed:
            self.readiness.state = 'blocked'
            reason = 'Mandatory audit checks failed or are missing.'
            if reason not in self.readiness.reasons:
                self.readiness.reasons.append(reason)

    @property
    def zero_order(self) -> Optional[PerturbationTerm]:
        """The trunk — the answer the dominant terms alone give."""
        return next((t for t in self.perturbation if t.order == ORDER_ZERO), None)

    @property
    def corrections(self) -> list[PerturbationTerm]:
        """Same-model corrections may change the action."""
        return [t for t in self.perturbation if t.order == ORDER_FIRST]

    @property
    def overturns(self) -> list[PerturbationTerm]:
        """Overturn term. Not a correction — each is a different zero-order model. These are
        what the flip test asks about: what could reverse the conclusion."""
        return [t for t in self.perturbation if t.order == ORDER_OVERTURN]

    @property
    def dropped(self) -> list[PerturbationTerm]:
        """Alternatives removed by dominance under the stated assumptions."""
        return [t for t in self.perturbation if t.order == ORDER_DROPPED]

    @property
    def hard_constraints(self) -> list[PerturbationTerm]:
        """Hard constraint. Conditions under which no zero-order answer exists at all."""
        return [t for t in self.perturbation if t.order == ORDER_HARD]

    @property
    def assumptions_to_confirm(self) -> list[SensitivityEntry]:
        """Legacy sensitivity flags; these are not proof of complete coverage."""
        return [s for s in self.sensitivity if s.decision_changed]

    @property
    def analysis_is_complete(self) -> bool:
        """Deprecated compatibility alias; no claim that deliberation is exhausted."""
        return self.readiness.state == "ready_under_stated_conditions" and self.audit.passed

    @property
    def execution_note(self) -> str:
        self._sync_audit_status()
        if not self.audit.passed:
            return "Readiness: blocked. Mandatory audit failure or incomplete coverage: " + ", ".join(
                [r.invariant_id for r in self.audit.failures] + self.audit.missing_checks) + ". No external action is authorized."
        reasons = "; ".join(self.readiness.reasons)
        return (f"Readiness: {self.readiness.state}. {reasons} "
                "This assessment does not authorize an external action.")

    def to_dict(self) -> dict:
        self._sync_audit_status()
        d = asdict(self)
        d["audit"]["missing_checks"] = self.audit.missing_checks
        d["analysis_is_complete"] = self.analysis_is_complete
        d["execution_note"] = self.execution_note
        return json_presentation(d)

    def to_markdown(self) -> str:
        lines = [
            f"## Decision",
        ]
        if self.action:
            lines.append(f"**{self.action}**")
            lines.append("")
            lines.append(f"Machine-readable: `{self.decision}`")
        else:
            lines.append(f"**{self.decision}**")
        lines += [
            "",
            f"## Formula",
            f"- Name: {self.formula_name}",
            f"- Citation: `{self.citation}`",
            f"- LaTeX: `{self.formula_latex}`",
            "",
            f"## Numeric",
        ]
        for k, v in self.numeric.items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## Assumptions"]
        for k, v in self.assumptions.items():
            lines.append(f"- {k}: {v}")
        lines += ["", "## Sensitivity"]
        for s in self.sensitivity:
            lines.append(
                f"- {s.assumption} ({s.perturbation}): "
                f"{'CHANGED' if s.decision_changed else 'stable'} → {s.new_decision} [{s.fragility}]"
            )
        lines += ["", "## Audit"]
        status = "PASS" if self.audit.passed else "FAIL"
        lines.append(f"Status: **{status}**")
        for r in self.audit.results:
            mark = "✓" if r.passed else "✗"
            lines.append(f"- [{mark}] {r.invariant_id} {r.name}: {r.message}")

        if self.perturbation:
            lines += ["", "## Zero-order expansion", ""]
            lines.append("| Order | Term | Value | Δ vs trunk | Citation |")
            lines.append("|---|---|---|---|---|")
            for t in self.perturbation:
                shift = "—" if t.relative_shift is None else f"{t.relative_shift:+.0%}"
                lines.append(
                    f"| {t.gloss} | {t.label} | {t.value} | {shift} | `{t.citation}` |"
                )
            notes = [t for t in self.perturbation if t.note]
            if notes:
                lines.append("")
                for t in notes:
                    lines.append(f"- **{t.label}** — {t.note}")

        lines += ["", "## Readiness", self.execution_note]
        lines += [f"- Missing check: {name}" for name in self.audit.missing_checks]
        lines += [f"- Condition: {condition}" for condition in self.readiness.conditions_of_use]
        lines += [f"- Reopen when: {trigger}" for trigger in self.readiness.reopening_triggers]
        pending = self.assumptions_to_confirm
        if self.analysis_is_complete and pending:
            for s in pending:
                lines.append(
                    f"- **{s.assumption}** — if {s.perturbation}, the decision "
                    f"becomes {s.new_decision} [{s.fragility}]"
                )
        return "\n".join(lines)
