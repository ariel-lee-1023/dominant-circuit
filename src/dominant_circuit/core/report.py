"""Output Contract — six mandatory fields."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


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

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> list[InvariantResult]:
        return [r for r in self.results if not r.passed]


@dataclass
class SensitivityEntry:
    assumption: str
    perturbation: str
    new_decision: Any
    decision_changed: bool
    fragility: str


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

    @property
    def assumptions_to_confirm(self) -> list[SensitivityEntry]:
        """The elicited assumptions that would change the decision if they turn
        out to be wrong. These are factual risks, not analytical ones: no further
        computation resolves them, only checking the world."""
        return [s for s in self.sensitivity if s.decision_changed]

    @property
    def analysis_is_complete(self) -> bool:
        """True when no further analysis can improve this answer.

        The contract was complete (dispatch would have raised otherwise), the
        assumption set is covered by the corpus, and every validation invariant
        passed. What remains is not more thinking — it is confirming the facts
        listed in `assumptions_to_confirm` and then acting.
        """
        return self.audit.passed

    @property
    def execution_note(self) -> str:
        """Plain-language answer to 'may I stop analyzing and start executing?'"""
        if not self.analysis_is_complete:
            failed = ", ".join(f.invariant_id for f in self.audit.failures)
            return (
                f"DO NOT EXECUTE. The audit failed ({failed}). This decision is not "
                "actionable; re-elicit the implicated fields and re-run."
            )
        pending = self.assumptions_to_confirm
        if not pending:
            return (
                "EXECUTE. The analysis is complete and no elicited assumption, if "
                "changed, alters this decision. Further deliberation cannot improve it."
            )
        names = ", ".join(sorted({s.assumption for s in pending}))
        return (
            "EXECUTE once you have confirmed: " + names + ". "
            "The analysis itself is complete — these are facts to check, not further "
            "calculations to run. If they hold as elicited, stop analyzing and act."
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["analysis_is_complete"] = self.analysis_is_complete
        d["execution_note"] = self.execution_note
        return d

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

        lines += ["", "## Execute", self.execution_note]
        pending = self.assumptions_to_confirm
        if self.analysis_is_complete and pending:
            for s in pending:
                lines.append(
                    f"- **{s.assumption}** — if {s.perturbation}, the decision "
                    f"becomes {s.new_decision} [{s.fragility}]"
                )
        return "\n".join(lines)
